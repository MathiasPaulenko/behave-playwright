"""Unit tests for the locator resolution cascade."""

from __future__ import annotations

from typing import Any

from behave_playwright.locators import resolve


class FakeLocator:
    """Records which strategy produced it; ``or_`` merges the trail."""

    def __init__(self, tag: str, trail: list[str] | None = None) -> None:
        self.trail = trail or [tag]

    def or_(self, other: FakeLocator) -> FakeLocator:
        return FakeLocator("", self.trail + other.trail)

    @property
    def first(self) -> FakeLocator:
        return self


class FakePage:
    def get_by_role(self, role: str, **kwargs: Any) -> FakeLocator:
        return FakeLocator(f"role:{role}")

    def get_by_label(self, text: str) -> FakeLocator:
        return FakeLocator("label")

    def get_by_placeholder(self, text: str) -> FakeLocator:
        return FakeLocator("placeholder")

    def get_by_text(self, text: str) -> FakeLocator:
        return FakeLocator("text")

    def get_by_test_id(self, test_id: str) -> FakeLocator:
        return FakeLocator("testid")

    def get_by_title(self, text: str) -> FakeLocator:
        return FakeLocator("title")

    def get_by_alt_text(self, text: str) -> FakeLocator:
        return FakeLocator("alt")

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(f"locator:{selector}")


def trails(page: FakePage, target: str, kind: Any = "action") -> list[str]:
    return resolve(page, target, kind).trail  # type: ignore[attr-defined]


def test_explicit_css() -> None:
    assert trails(FakePage(), "css=#foo .bar") == ["locator:css=#foo .bar"]


def test_explicit_xpath_prefix_and_shorthand() -> None:
    assert trails(FakePage(), "xpath=//div") == ["locator:xpath=//div"]
    assert trails(FakePage(), "//div[@id='x']") == ["locator:xpath=//div[@id='x']"]


def test_explicit_text_and_testid() -> None:
    assert trails(FakePage(), "text=Hello") == ["text"]
    assert trails(FakePage(), "testid=submit") == ["testid"]
    assert trails(FakePage(), "test-id=submit") == ["testid"]
    assert trails(FakePage(), "data-testid=submit") == ["testid"]


def test_explicit_label_placeholder_title_alt() -> None:
    assert trails(FakePage(), "label=Email") == ["label"]
    assert trails(FakePage(), "placeholder=Search") == ["placeholder"]
    assert trails(FakePage(), "title=Logo") == ["title"]
    assert trails(FakePage(), "alt=Avatar") == ["alt"]


def test_explicit_role_with_and_without_name() -> None:
    assert trails(FakePage(), "role=button:Save") == ["role:button"]
    assert trails(FakePage(), "role=navigation") == ["role:navigation"]


def test_action_cascade() -> None:
    trail = trails(FakePage(), "Sign in")
    assert "role:button" in trail
    assert "role:link" in trail
    assert "text" in trail
    assert "testid" in trail
    assert "locator:Sign in" in trail


def test_field_cascade() -> None:
    trail = trails(FakePage(), "Email", "field")
    assert "label" in trail
    assert "placeholder" in trail
    assert "role:textbox" in trail
    assert "role:combobox" in trail
    assert "testid" in trail
    assert "locator:Email" in trail


def test_any_cascade() -> None:
    trail = trails(FakePage(), "#main", "any")
    assert "testid" in trail
    assert "text" in trail
    assert "locator:#main" in trail
    assert not any(t.startswith("role:") for t in trail)
