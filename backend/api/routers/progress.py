import json
import uuid
from typing import Annotated

import redis
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import ValidationError

from api.schemas.progress import Progress
from api.services import progress_service

router = APIRouter(prefix="/progress", tags=["progress"])

# 사용자를 구분하는 쿠키 이름입니다. 로그인이 없어 브라우저마다 익명 ID를 하나씩 줍니다.
COOKIE_NAME = "progress_id"

# 쿠키 유효 기간(180일). 요청할 때마다 다시 180일로 늘립니다.
COOKIE_MAX_AGE = 60 * 60 * 24 * 180

REDIS_ERROR_RESPONSE = {
    "description": "기록 저장소(Redis)에 연결하지 못한 경우입니다. 화면은 기록 없이 계속 사용할 수 있습니다.",
}

# 쿠키는 브라우저가 자동으로 보내므로 Swagger 입력칸에는 보이지 않게 합니다.
ProgressCookie = Annotated[str | None, Cookie(include_in_schema=False)]


def _is_valid_id(value: str) -> bool:
    """서버가 발급한 모양(uuid4, 32자리 16진수)인지 확인합니다."""
    try:
        return uuid.UUID(value).hex == value
    except ValueError:
        return False


def _use_cookie(progress_id: str | None, response: Response) -> str:
    """쿠키 ID가 없거나 모양이 잘못되었으면 새로 발급합니다. 유효 기간은 매번 다시 늘립니다."""
    if progress_id is None or not _is_valid_id(progress_id):
        progress_id = uuid.uuid4().hex
    response.set_cookie(
        COOKIE_NAME,
        progress_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return progress_id


def _redis_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="기록 저장소에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.")


@router.get(
    "",
    response_model=Progress,
    summary="사용자 진행 상태 조회",
    description=(
        "이 브라우저에 저장된 트레이너 화면 진행 상태를 조회합니다.\n\n"
        "**사용자 구분**\n"
        "- 로그인 없이 쿠키(`progress_id`)로 구분합니다. 처음 요청 때 서버가 발급하고, 이후 브라우저가 자동으로 보냅니다.\n"
        "- 같은 브라우저에서만 기록이 이어집니다. 쿠키를 지우면 새 사용자로 시작합니다.\n\n"
        "**기록이 없을 때**\n"
        "- 처음 상태(버전 `null`, 열린 체육관 1개, 챔피언 잠김, 깬 N 스토리 0개)를 반환합니다."
    ),
    response_description="저장된 진행 상태 (없으면 처음 상태)",
    responses={503: REDIS_ERROR_RESPONSE},
)
def read_progress(response: Response, progress_id: ProgressCookie = None):
    progress_id = _use_cookie(progress_id, response)
    try:
        data = progress_service.get_progress(progress_id)
    except redis.RedisError:
        raise _redis_unavailable()
    except json.JSONDecodeError:
        # 저장된 기록이 깨져 JSON으로 읽을 수 없으면 처음 상태로 돌려줍니다.
        return Progress()
    if data is None:
        return Progress()
    try:
        return Progress.model_validate(data)
    except ValidationError:
        # 저장 모양이 바뀌기 전에 남은 예전 기록이면 처음 상태로 돌려줍니다.
        return Progress()


@router.put(
    "",
    response_model=Progress,
    summary="사용자 진행 상태 저장",
    description=(
        "이 브라우저의 트레이너 화면 진행 상태를 저장합니다.\n\n"
        "**저장 방식**\n"
        "- 보낸 값으로 기록 전체를 바꿉니다. 보내지 않은 값은 처음 상태로 저장되므로 네 값을 모두 보내 주세요.\n"
        "- 저장할 때마다 보관 기간이 90일로 다시 늘어납니다.\n\n"
        "**값 범위**\n"
        "- `version`: `black`, `white`, `null`\n"
        "- `gym_unlocked`: 1~8\n"
        "- `n_story_cleared`: 0~6\n"
        "- 범위를 벗어나거나 정해지지 않은 값이 있으면 저장하지 않고 422를 반환합니다."
    ),
    response_description="저장된 진행 상태",
    responses={
        422: {"description": "값의 범위를 벗어났거나 정해지지 않은 값을 보낸 경우입니다."},
        503: REDIS_ERROR_RESPONSE,
    },
)
def update_progress(progress: Progress, response: Response, progress_id: ProgressCookie = None):
    progress_id = _use_cookie(progress_id, response)
    try:
        progress_service.save_progress(progress_id, progress.model_dump())
    except redis.RedisError:
        raise _redis_unavailable()
    return progress


@router.delete(
    "",
    status_code=204,
    summary="사용자 진행 상태 초기화",
    description=(
        "이 브라우저의 진행 상태 기록을 지웁니다.\n\n"
        "- 지운 뒤 조회하면 처음 상태를 반환합니다.\n"
        "- 기록이 없어도 오류 없이 처리합니다."
    ),
    response_description="초기화 완료 (본문 없음)",
    responses={503: REDIS_ERROR_RESPONSE},
)
def reset_progress(response: Response, progress_id: ProgressCookie = None):
    progress_id = _use_cookie(progress_id, response)
    try:
        progress_service.delete_progress(progress_id)
    except redis.RedisError:
        raise _redis_unavailable()
