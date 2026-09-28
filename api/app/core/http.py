import ssl

import httpx


def external_client() -> httpx.AsyncClient:
    # Use OS trust roots, including managed Windows CAs, without disabling TLS.
    return httpx.AsyncClient(verify=ssl.create_default_context(), timeout=15.0)
