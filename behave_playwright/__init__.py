"""behave-playwright: BDD web testing with Behave and Playwright."""

import importlib.metadata

from behave_playwright.config import BrowserConfig

try:
    __version__ = importlib.metadata.version("behave-playwright")
except importlib.metadata.PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+unknown"

__all__ = ["BrowserConfig", "__version__"]
