from dataclasses import dataclass


@dataclass
class AppError(Exception):
    status_code: int
    code: str
    message: str
    retry_after: int | None = None


class UpstreamError(AppError):
    def __init__(
        self, message: str = "O catálogo de livros está indisponível no momento."
    ) -> None:
        super().__init__(502, "UPSTREAM_ERROR", message)


class UpstreamTimeout(AppError):
    def __init__(self) -> None:
        super().__init__(
            504,
            "UPSTREAM_TIMEOUT",
            "A consulta ao catálogo demorou demais. Tente novamente.",
        )


class UpstreamRateLimited(AppError):
    def __init__(self) -> None:
        super().__init__(
            503,
            "SERVICE_UNAVAILABLE",
            "O catálogo está ocupado. Tente novamente em instantes.",
            5,
        )
