"""Safe error codes; never include provider bodies, credentials or user content."""


class ProviderError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ProviderUnavailable(ProviderError):
    def __init__(self) -> None:
        super().__init__("ai_unavailable")


class ProviderTimeout(ProviderError):
    def __init__(self) -> None:
        super().__init__("ai_timeout")


class InvalidProviderOutput(ProviderError):
    def __init__(self) -> None:
        super().__init__("ai_invalid_output")


class ProviderRefusal(ProviderError):
    def __init__(self) -> None:
        super().__init__("ai_refusal")
