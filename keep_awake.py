
"""Check and wake a Streamlit Community Cloud app with a headless browser."""

import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

READY_TEXT = "Support Intelligence"
WAKE_BUTTON_TEXT = "get this app back up"

ATTEMPTS = 3
NAVIGATION_TIMEOUT_MS = 30_000
CHECK_DURATION_SECONDS = 45


def get_contexts(page):
    """Return the main page and any available frames."""
    return [page] + [
        frame for frame in page.frames
        if frame != page.main_frame
    ]


def main(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 900}
        )
        page.set_default_timeout(5_000)

        try:
            for attempt in range(1, ATTEMPTS + 1):
                print(f"[{attempt}/{ATTEMPTS}] Opening {url}", flush=True)

                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=NAVIGATION_TIMEOUT_MS,
                    )
                except PlaywrightTimeout:
                    print(
                        "Navigation timed out; checking the page anyway.",
                        flush=True,
                    )
                except Exception as exc:
                    print(f"Navigation error: {exc}", flush=True)
                    continue

                deadline = time.monotonic() + CHECK_DURATION_SECONDS
                wake_clicked = False

                while time.monotonic() < deadline:
                    for ctx in get_contexts(page):
                        try:
                            wake_button = ctx.get_by_role(
                                "button",
                                name=WAKE_BUTTON_TEXT,
                                exact=False,
                            )

                            if (
                                not wake_clicked
                                and wake_button.count() > 0
                                and wake_button.first.is_visible()
                            ):
                                print(
                                    "App sleep screen found; clicking wake button.",
                                    flush=True,
                                )
                                wake_button.first.click(timeout=5_000)
                                wake_clicked = True
                                time.sleep(3)
                                continue

                            ready = ctx.get_by_text(
                                READY_TEXT,
                                exact=False,
                            )

                            if (
                                ready.count() > 0
                                and ready.first.is_visible()
                            ):
                                print(
                                    "SUCCESS: App content is visible.",
                                    flush=True,
                                )
                                time.sleep(5)
                                return 0

                        except Exception:
                            # The page or a frame may still be loading.
                            continue

                    time.sleep(2)

                print(
                    f"Attempt {attempt} timed out. Retrying if possible.",
                    flush=True,
                )

            print(
                "FAILED: The expected app text was not detected. "
                "Check the page output and confirm READY_TEXT matches "
                "a visible heading in your app.",
                flush=True,
            )

            try:
                print(f"Final page title: {page.title()}", flush=True)
                print(f"Final page URL: {page.url}", flush=True)
                print(
                    "Page text preview: "
                    + page.locator("body").inner_text(timeout=5_000)[:1500],
                    flush=True,
                )
            except Exception as exc:
                print(f"Could not inspect final page: {exc}", flush=True)

            return 1

        finally:
            browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python keep_awake.py <app-url>")

    sys.exit(main(sys.argv[1]))
