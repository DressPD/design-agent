"""Take screenshots of deployed sites using Playwright."""

import json
from pathlib import Path

from strands import tool

VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "mobile": {"width": 375, "height": 812},
}


@tool
def take_screenshots(
    url: str,
    project_name: str,
    viewports: str = "desktop,mobile",
    full_page: bool = True,
) -> str:
    """Capture screenshots of a deployed website at specified viewport sizes.

    Takes screenshots at desktop (1920x1080) and mobile (375x812) viewports by default.
    Screenshots are saved to /tmp/design-agent-screenshots/{project_name}/.

    Args:
        url: The URL to screenshot (e.g. https://d123abc.cloudfront.net).
        project_name: Project identifier for organizing screenshot files.
        viewports: Comma-separated viewport names: 'desktop', 'mobile', or 'desktop,mobile'.
        full_page: Whether to capture the full scrollable page (default True).

    Returns:
        JSON with file paths to saved screenshots.
    """
    from playwright.sync_api import sync_playwright

    output_dir = Path(f"/tmp/design-agent-screenshots/{project_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    requested = [v.strip() for v in viewports.split(",")]
    screenshots: list[dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for viewport_name in requested:
            vp = VIEWPORTS.get(viewport_name)
            if not vp:
                continue

            page = browser.new_page(viewport_size=vp)
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            filename = f"{viewport_name}.png"
            filepath = output_dir / filename
            page.screenshot(path=str(filepath), full_page=full_page)

            screenshots.append({
                "viewport": viewport_name,
                "width": str(vp["width"]),
                "height": str(vp["height"]),
                "path": str(filepath),
            })

            page.close()

        browser.close()

    return json.dumps({
        "project_name": project_name,
        "url": url,
        "screenshots": screenshots,
    })
