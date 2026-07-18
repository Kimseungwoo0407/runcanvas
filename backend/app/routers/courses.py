from __future__ import annotations

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import PlainTextResponse

from app.dependencies import DB, CurrentUser
from app.schemas.course import (
    CourseCreateRequest,
    CourseDetail,
    CourseListResponse,
    CoursePatchRequest,
)
from app.services.course import CourseService

router = APIRouter(tags=["courses"])


@router.post("/courses", response_model=CourseDetail, status_code=status.HTTP_201_CREATED)
def create_course(request: CourseCreateRequest, user: CurrentUser, db: DB) -> CourseDetail:
    return CourseService(db).create(user.id, request)


@router.get("/courses", response_model=CourseListResponse)
def list_courses(
    user: CurrentUser,
    db: DB,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    q: str | None = Query(default=None, max_length=120),
    favorite: bool | None = None,
) -> CourseListResponse:
    return CourseService(db).list(user.id, limit=limit, cursor=cursor, query=q, favorite=favorite)


@router.get("/courses/{course_id}", response_model=CourseDetail)
def get_course(course_id: str, user: CurrentUser, db: DB) -> CourseDetail:
    return CourseService(db).get(user.id, course_id)


@router.patch("/courses/{course_id}", response_model=CourseDetail)
def patch_course(
    course_id: str,
    request: CoursePatchRequest,
    user: CurrentUser,
    db: DB,
) -> CourseDetail:
    return CourseService(db).patch(user.id, course_id, request)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: str, user: CurrentUser, db: DB) -> Response:
    CourseService(db).delete(user.id, course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/courses/{course_id}/clone", response_model=CourseDetail, status_code=status.HTTP_201_CREATED)
def clone_course(course_id: str, user: CurrentUser, db: DB) -> CourseDetail:
    return CourseService(db).clone(user.id, course_id)


@router.get("/courses/{course_id}/gpx", response_class=PlainTextResponse)
def download_gpx(course_id: str, user: CurrentUser, db: DB) -> PlainTextResponse:
    filename, content = CourseService(db).gpx(user.id, course_id)
    return PlainTextResponse(
        content,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/shared/courses/{token}", response_model=CourseDetail)
def shared_course(token: str, db: DB) -> CourseDetail:
    return CourseService(db).get_shared(token)


@router.post(
    "/shared/courses/{token}/clone",
    response_model=CourseDetail,
    status_code=status.HTTP_201_CREATED,
)
def clone_shared_course(token: str, user: CurrentUser, db: DB) -> CourseDetail:
    return CourseService(db).clone_shared(user.id, token)
