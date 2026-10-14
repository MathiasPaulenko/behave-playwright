"""Bundled behave step definitions powered by Playwright.

Register them from a module inside ``features/steps/``::

    # features/steps/behave_playwright_steps.py
    import behave_playwright.steps  # noqa: F401 — registration happens on import

or call :func:`use_steps` from ``environment.py``.
"""

from behave_playwright.steps import (
    assertions,
    browser,
    interaction,
    navigation,
    network,
    session,
    waiting,
)

__all__ = [
    "assertions",
    "browser",
    "interaction",
    "navigation",
    "network",
    "session",
    "use_steps",
    "waiting",
]


def use_steps() -> None:
    """Import all bundled step modules so their definitions register.

    Importing this package already does the same; this exists so an
    ``environment.py`` can express the intent explicitly.
    """
