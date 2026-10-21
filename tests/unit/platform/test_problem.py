import pytest

from app.platform.errors import (
    DomainError,
    Problem,
    internal_error,
    method_not_allowed,
    not_found,
    not_ready,
)


def test_problem_has_rfc9457_fields_and_code() -> None:
    """AC-12: type, title, status, detail and code."""
    problem = Problem(
        status=409, code="leave.overlap", title="Çakışma", detail="Tarihler çakışıyor."
    )
    assert problem.to_dict() == {
        "type": "urn:polsan:plm:problem:leave.overlap",
        "title": "Çakışma",
        "status": 409,
        "detail": "Tarihler çakışıyor.",
        "code": "leave.overlap",
    }


@pytest.mark.parametrize(
    ("problem", "status", "title", "detail"),
    [
        (not_found(), 404, "Bulunamadı", "İstenen adres bulunamadı."),
        (
            method_not_allowed(),
            405,
            "Yöntem desteklenmiyor",
            "Bu adres, istekte kullanılan yöntemi desteklemiyor.",
        ),
        (
            internal_error("c1"),
            500,
            "Beklenmeyen bir hata oluştu",
            "İsteğiniz işlenirken beklenmeyen bir hata oluştu. Sorun sürerse bu kimlikle "
            "destek ekibine başvurun.",
        ),
        (
            not_ready(),
            503,
            "Hizmet hazır değil",
            "Sistem şu anda istekleri karşılamaya hazır değil.",
        ),
    ],
)
def test_platform_problems_are_turkish_and_coded(
    problem: Problem, status: int, title: str, detail: str
) -> None:
    """AC-12..14, R-5 (VERIFY V2, review F-1): the Turkish title and detail are the contract."""
    assert problem.status == status
    assert problem.code.startswith("platform.")
    assert problem.title == title
    assert problem.detail == detail


def test_internal_error_carries_only_the_correlation_id() -> None:
    """AC-14: the id is the only addition to the standard fields."""
    body = internal_error("abc-1").to_dict()
    assert body["correlation_id"] == "abc-1"
    assert set(body) == {"type", "title", "status", "detail", "code", "correlation_id"}


def test_domain_error_subclass_becomes_its_problem() -> None:
    class InsufficientBalance(DomainError):
        code = "leave.insufficient_balance"
        status = 409
        title = "Yetersiz bakiye"

    problem = InsufficientBalance("Bakiye yetersiz.").to_problem()
    assert (problem.status, problem.code, problem.title, problem.detail) == (
        409,
        "leave.insufficient_balance",
        "Yetersiz bakiye",
        "Bakiye yetersiz.",
    )
