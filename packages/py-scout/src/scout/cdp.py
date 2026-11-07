"""Attach to the user's own Chrome (started with --remote-debugging-port) over CDP."""

import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page, async_playwright

from scout.config import get_settings


class ScoutError(RuntimeError):
    pass


def endpoint() -> str:
    settings = get_settings()
    if settings.cdp_url:
        return settings.cdp_url
    # Chrome rejects non-IP Host headers, so resolve host.docker.internal here
    try:
        host = socket.gethostbyname("host.docker.internal")
    except OSError:
        host = "127.0.0.1"  # running on the Mac itself
    return f"http://{host}:{settings.cdp_port}"


@asynccontextmanager
async def connect() -> AsyncIterator[Browser]:
    url = endpoint()
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(url)
        except Exception as e:
            raise ScoutError(f"No Chrome with remote debugging at {url}: {e}") from e
        # leaving the block only drops the connection; the user's Chrome keeps running
        yield browser


def pages(browser: Browser) -> list[Page]:
    return [page for context in browser.contexts for page in context.pages]
