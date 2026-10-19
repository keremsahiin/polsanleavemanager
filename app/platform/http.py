"""HTTP plumbing shared by every route (docs/conventions.md, Error handling)."""

from fastapi.responses import JSONResponse

from app.platform.errors import PROBLEM_MEDIA_TYPE, Problem


def problem_response(problem: Problem) -> JSONResponse:
    return JSONResponse(
        problem.to_dict(), status_code=problem.status, media_type=PROBLEM_MEDIA_TYPE
    )
