import httpx

USER_AGENT = "play/1.0 (+https://yan.fi)"


def client(timeout: float = 15) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
    )
