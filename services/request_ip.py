from fastapi import Request


def get_client_ip(request: Request) -> str:
    """За reverse-proxy (Oracle Cloud + nginx/Caddy) справжня IP клієнта приходить
    у заголовку X-Forwarded-For, а не в request.client.host (це буде IP проксі)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
