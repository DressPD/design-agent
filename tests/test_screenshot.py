import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call


@pytest.fixture
def mock_playwright():
    mock_page = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_p = MagicMock()
    mock_p.chromium.launch.return_value = mock_browser
    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__ = MagicMock(return_value=mock_p)
    mock_sync_playwright.return_value.__exit__ = MagicMock(return_value=False)
    return mock_sync_playwright, mock_p, mock_browser, mock_page


class TestTakeScreenshots:
    def test_returns_json_with_screenshots(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, _, _ = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            result = take_screenshots("https://example.com", "myproject")
        data = json.loads(result)
        assert data["project_name"] == "myproject"
        assert data["url"] == "https://example.com"
        assert "screenshots" in data

    def test_desktop_viewport_dimensions(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            result = take_screenshots("https://example.com", "myproject", viewports="desktop")
        data = json.loads(result)
        assert len(data["screenshots"]) == 1
        assert data["screenshots"][0]["width"] == "1920"
        assert data["screenshots"][0]["height"] == "1080"

    def test_mobile_viewport_dimensions(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            result = take_screenshots("https://example.com", "myproject", viewports="mobile")
        data = json.loads(result)
        assert len(data["screenshots"]) == 1
        assert data["screenshots"][0]["width"] == "375"
        assert data["screenshots"][0]["height"] == "812"

    def test_both_viewports_by_default(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            result = take_screenshots("https://example.com", "myproject")
        data = json.loads(result)
        assert len(data["screenshots"]) == 2
        viewport_names = {s["viewport"] for s in data["screenshots"]}
        assert viewport_names == {"desktop", "mobile"}

    def test_skips_unknown_viewport(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            result = take_screenshots("https://example.com", "myproject", viewports="desktop,tablet,mobile")
        data = json.loads(result)
        viewport_names = {s["viewport"] for s in data["screenshots"]}
        assert "tablet" not in viewport_names
        assert "desktop" in viewport_names
        assert "mobile" in viewport_names

    def test_calls_page_goto_with_url(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            take_screenshots("https://example.com", "myproject", viewports="desktop")
        mock_page.goto.assert_called_with("https://example.com", wait_until="networkidle", timeout=30000)

    def test_calls_page_screenshot(self, tmp_path, mock_playwright):
        mock_sync_playwright, _, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            take_screenshots("https://example.com", "myproject", viewports="desktop", full_page=True)
        mock_page.screenshot.assert_called_once()
        call_kwargs = mock_page.screenshot.call_args[1]
        assert call_kwargs["full_page"] is True

    def test_launches_chromium_headless(self, tmp_path, mock_playwright):
        mock_sync_playwright, mock_p, mock_browser, mock_page = mock_playwright
        with patch("playwright.sync_api.sync_playwright", mock_sync_playwright):
            from src.tools.screenshot import take_screenshots
            take_screenshots("https://example.com", "myproject", viewports="desktop")
        mock_p.chromium.launch.assert_called_with(headless=True)
