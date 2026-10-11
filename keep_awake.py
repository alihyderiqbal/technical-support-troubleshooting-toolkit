"""Keeps the Streamlit Community Cloud app awake.

Streamlit puts apps to sleep after a period with no real visitors. A plain HTTP request does not count, so this
opens the app in a headless browser (a real session), wakes it if it is asleep, and waits until the page renders.

Usage: python scripts/keep_awake.py https://your-app.streamlit.app
"""
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

WAKE_BUTTON_TEXT = "get this app back up"
READY_TEXT = "Support Intelligence"
MAX_WAIT_MS = 180_000


def frames(page):
    """The app renders on the page itself or, on Community Cloud, inside an iframe."""
    return [page] + [f for f in page.frames if f != page.main_frame]


def main(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for attempt in range(1, 4):
            print(f"[{attempt}/3] opening {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            deadline = time.time() + MAX_WAIT_MS / 1000
            while time.time() < deadline:
                for ctx in frames(page):
                    try:
                        button = ctx.get_by_role("button", name=WAKE_BUTTON_TEXT, exact=False)
                        if button.count() and button.first.is_visible():
                            print("app was asleep - waking it")
                            button.first.click()
                            time.sleep(5)
                    except Exception:
                        pass
                    try:
                        if ctx.get_by_text(READY_TEXT, exact=False).first.is_visible():
                            print("app is awake and rendered")
                            time.sleep(8)  # keep the session open briefly so it registers as a real visit
                            browser.close()
                            return 0
                    except Exception:
                        pass
                time.sleep(3)
            print("timed out waiting for the app to render - retrying")
        browser.close()
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: keep_awake.py <app-url>")
    sys.exit(main(sys.argv[1]))
