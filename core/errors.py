"""Типизированные ошибки. `kind` определяет экран ошибки в интерфейсе;
`detail` идёт только в лог и пользователю не показывается."""


class CheckError(Exception):
    kind = "unknown"
    retryable = False

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail


class UnsupportedFormat(CheckError):
    kind = "unsupported_format"


class FileTooLarge(CheckError):
    kind = "too_large"


class EmptyFile(CheckError):
    kind = "empty_file"


class CorruptedFile(CheckError):
    kind = "corrupted_file"


class ReadFailure(CheckError):
    kind = "read_failed"
    retryable = True


class LLMUnavailable(CheckError):
    kind = "llm_unavailable"
    retryable = True


class LLMFailure(CheckError):
    kind = "llm_failed"
    retryable = True


class InvalidModelResponse(CheckError):
    kind = "bad_response"
    retryable = True


class CodeCheckFailure(CheckError):
    kind = "code_check_failed"
    retryable = True


class RubricProblem(CheckError):
    kind = "rubric_problem"
