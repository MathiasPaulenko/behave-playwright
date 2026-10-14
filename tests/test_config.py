"""Tests for BrowserConfig resolution from userdata and env vars."""

import pytest

from behave_playwright import BrowserConfig


def test_defaults() -> None:
    config = BrowserConfig.from_sources({}, {})
    assert config.browser == "chromium"
    assert config.headless is True
    assert config.base_url is None
    assert config.viewport_width is None
    assert config.viewport_height is None
    assert config.device is None
    assert config.locale is None
    assert config.timeout == 30_000.0
    assert config.screenshots_on_failure is True


def test_userdata_overrides() -> None:
    config = BrowserConfig.from_sources(
        {
            "browser": "firefox",
            "headless": "false",
            "base_url": "http://localhost:8000",
            "viewport": "1920x1080",
            "locale": "es-ES",
            "slow_mo": "250",
            "timeout": "5000",
        },
        {},
    )
    assert config.browser == "firefox"
    assert config.headless is False
    assert config.base_url == "http://localhost:8000"
    assert config.viewport_width == 1920
    assert config.viewport_height == 1080
    assert config.locale == "es-ES"
    assert config.slow_mo == 250.0
    assert config.timeout == 5000.0


def test_env_vars_used_when_no_userdata() -> None:
    config = BrowserConfig.from_sources(
        {}, {"BEHAVE_PW_BROWSER": "webkit", "BEHAVE_PW_HEADLESS": "0"}
    )
    assert config.browser == "webkit"
    assert config.headless is False


def test_userdata_beats_env() -> None:
    config = BrowserConfig.from_sources({"browser": "firefox"}, {"BEHAVE_PW_BROWSER": "webkit"})
    assert config.browser == "firefox"


def test_namespaced_userdata_key() -> None:
    config = BrowserConfig.from_sources({"behave_playwright.browser": "webkit"}, {})
    assert config.browser == "webkit"


def test_plain_userdata_beats_namespaced() -> None:
    config = BrowserConfig.from_sources(
        {"browser": "firefox", "behave_playwright.browser": "webkit"}, {}
    )
    assert config.browser == "firefox"


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes", "on"])
def test_bool_true_variants(raw: str) -> None:
    assert BrowserConfig.from_sources({"headless": raw}, {}).headless is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "off"])
def test_bool_false_variants(raw: str) -> None:
    assert BrowserConfig.from_sources({"headless": raw}, {}).headless is False


def test_invalid_bool() -> None:
    with pytest.raises(ValueError, match="headless"):
        BrowserConfig.from_sources({"headless": "maybe"}, {})


def test_invalid_browser() -> None:
    with pytest.raises(ValueError, match="netscape"):
        BrowserConfig.from_sources({"browser": "netscape"}, {})


def test_invalid_viewport() -> None:
    with pytest.raises(ValueError, match="viewport"):
        BrowserConfig.from_sources({"viewport": "wide"}, {})


def test_invalid_number() -> None:
    with pytest.raises(ValueError, match="timeout"):
        BrowserConfig.from_sources({"timeout": "soon"}, {})


def test_screenshots_disabled() -> None:
    config = BrowserConfig.from_sources({"screenshots": "false", "screenshots_dir": "shots"}, {})
    assert config.screenshots_on_failure is False
    assert config.screenshots_dir == "shots"


def test_zero_viewport_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        BrowserConfig.from_sources({"viewport": "0x720"}, {})


@pytest.mark.parametrize("key", ["timeout", "slow_mo"])
def test_negative_numbers_rejected(key: str) -> None:
    with pytest.raises(ValueError, match=key):
        BrowserConfig.from_sources({key: "-1"}, {})
