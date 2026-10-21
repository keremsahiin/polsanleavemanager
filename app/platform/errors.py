"""Coded errors and RFC 9457 problem details (docs/conventions.md, Error handling).

Pure: no web framework here, so domain code may raise DomainError subclasses.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

PROBLEM_MEDIA_TYPE = "application/problem+json"


@dataclass(frozen=True)
class Problem:
    status: int
    code: str
    title: str
    detail: str
    extensions: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "type": f"urn:polsan:plm:problem:{self.code}",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "code": self.code,
            **self.extensions,
        }


class DomainError(Exception):
    """Base of every coded business error; subclasses set code = '<module>.<snake_case>'."""

    code = "domain.error"
    status = 400
    title = "İşlem gerçekleştirilemedi"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail

    def to_problem(self) -> Problem:
        return Problem(status=self.status, code=self.code, title=self.title, detail=self.detail)


def not_found() -> Problem:
    return Problem(
        status=404,
        code="platform.not_found",
        title="Bulunamadı",
        detail="İstenen adres bulunamadı.",
    )


def method_not_allowed() -> Problem:
    return Problem(
        status=405,
        code="platform.method_not_allowed",
        title="Yöntem desteklenmiyor",
        detail="Bu adres, istekte kullanılan yöntemi desteklemiyor.",
    )


def internal_error(correlation_id: str) -> Problem:
    return Problem(
        status=500,
        code="platform.internal_error",
        title="Beklenmeyen bir hata oluştu",
        detail="İsteğiniz işlenirken beklenmeyen bir hata oluştu. Sorun sürerse bu kimlikle "
        "destek ekibine başvurun.",
        extensions={"correlation_id": correlation_id},
    )


def not_ready() -> Problem:
    return Problem(
        status=503,
        code="platform.not_ready",
        title="Hizmet hazır değil",
        detail="Sistem şu anda istekleri karşılamaya hazır değil.",
    )
