"""Element resolution for the bundled step definitions.

Steps accept a flexible ``target`` string. An explicit prefix always wins:

- ``css=<selector>`` or a raw CSS selector — ``page.locator()``
- ``xpath=<expr>`` or ``//...`` — XPath
- ``text=<txt>`` — ``get_by_text``
- ``testid=<id>`` / ``test-id=<id>`` / ``data-testid=<id>`` — ``get_by_test_id``
- ``label=<txt>`` — ``get_by_label``
- ``placeholder=<txt>`` — ``get_by_placeholder``
- ``title=<txt>`` — ``get_by_title``
- ``alt=<txt>`` — ``get_by_alt_text``
- ``role=<role>`` or ``role=<role>:<name>`` — ``get_by_role``

Without a prefix, a cascade combines Playwright's accessible selectors into a
single ``or_`` locator (role → label/placeholder → text → test id → CSS), so
steps work on semantic HTML without forcing ``data-testid`` everywhere.
"""

from __future__ import annotations

import re
from typing import Any, Literal, cast

from playwright.sync_api import Locator, Page

TargetKind = Literal["action", "field", "any"]

_ACTION_ROLES = (
    "button",
    "link",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "tab",
    "option",
    "radio",
    "checkbox",
    "switch",
    "treeitem",
)
_FIELD_ROLES = (
    "textbox",
    "combobox",
    "listbox",
    "checkbox",
    "radio",
    "switch",
    "slider",
    "spinbutton",
    "searchbox",
)

_PREFIX_RE = re.compile(
    r"^(css|xpath|text|testid|test-id|data-testid|label|placeholder|title|alt)=",
    re.DOTALL,
)
_ROLE_RE = re.compile(r"^role=([a-z]+)(?::(.*))?$", re.DOTALL | re.IGNORECASE)


def resolve(page: Page, target: str, kind: TargetKind = "action") -> Locator:
    """Resolve ``target`` into a locator. May match multiple elements."""
    target = target.strip()
    explicit = _explicit(page, target)
    if explicit is not None:
        return explicit
    if kind == "field":
        return _field_cascade(page, target)
    if kind == "any":
        return _any_cascade(page, target)
    return _action_cascade(page, target)


def resolve_first(page: Page, target: str, kind: TargetKind = "action") -> Locator:
    """Resolve ``target`` to a single-element locator (topmost DOM match)."""
    return resolve(page, target, kind).first


def _explicit(page: Page, target: str) -> Locator | None:
    if target.startswith("//"):
        return page.locator(f"xpath={target}")
    prefix_match = _PREFIX_RE.match(target)
    if prefix_match:
        prefix, value = prefix_match.group(1), target[prefix_match.end() :]
        if prefix in ("css", "xpath"):
            return page.locator(target)
        if prefix == "text":
            return page.get_by_text(value)
        if prefix in ("testid", "test-id", "data-testid"):
            return page.get_by_test_id(value)
        if prefix == "label":
            return page.get_by_label(value)
        if prefix == "placeholder":
            return page.get_by_placeholder(value)
        if prefix == "title":
            return page.get_by_title(value)
        return page.get_by_alt_text(value)
    role_match = _ROLE_RE.match(target)
    if role_match:
        role, name = role_match.group(1), role_match.group(2)
        role_lit = cast(Any, role)
        return page.get_by_role(role_lit, name=name) if name else page.get_by_role(role_lit)
    return None


def _action_cascade(page: Page, target: str) -> Locator:
    locator = page.get_by_role(cast(Any, _ACTION_ROLES[0]), name=target)
    for role in _ACTION_ROLES[1:]:
        locator = locator.or_(page.get_by_role(cast(Any, role), name=target))
    return (
        locator.or_(page.get_by_text(target))
        .or_(page.get_by_test_id(target))
        .or_(page.locator(target))
    )


def _field_cascade(page: Page, target: str) -> Locator:
    locator = page.get_by_label(target).or_(page.get_by_placeholder(target))
    for role in _FIELD_ROLES:
        locator = locator.or_(page.get_by_role(cast(Any, role), name=target))
    return locator.or_(page.get_by_test_id(target)).or_(page.locator(target))


def _any_cascade(page: Page, target: str) -> Locator:
    return page.get_by_test_id(target).or_(page.get_by_text(target)).or_(page.locator(target))
