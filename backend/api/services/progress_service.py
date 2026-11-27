import json
import os

import redis

# Redis 접속 주소. Docker Compose 안에서는 서비스 이름(redis)으로 접속합니다.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# 사용자 기록을 저장하는 키 앞부분입니다. 예: progress:<쿠키 ID>
KEY_PREFIX = "progress:"

# 마지막 저장 후 90일 동안 다시 저장하지 않으면 기록이 지워집니다.
TTL_SECONDS = 60 * 60 * 24 * 90

# 연결 정보만 만들어 둡니다. 실제 접속은 처음 명령을 보낼 때 일어납니다.
# Redis가 응답하지 않을 때 오래 기다리지 않도록 2초 제한을 둡니다.
redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def _key(progress_id: str) -> str:
    return f"{KEY_PREFIX}{progress_id}"


def get_progress(progress_id: str) -> dict | None:
    """저장된 기록을 반환합니다. 기록이 없으면 None을 반환합니다."""
    raw = redis_client.get(_key(progress_id))
    if raw is None:
        return None
    return json.loads(raw)


def save_progress(progress_id: str, data: dict) -> None:
    """기록을 통째로 바꿔 저장하고, 보관 기간을 다시 90일로 늘립니다."""
    redis_client.set(_key(progress_id), json.dumps(data, ensure_ascii=False), ex=TTL_SECONDS)


def delete_progress(progress_id: str) -> None:
    """기록을 지웁니다. 기록이 없어도 오류 없이 넘어갑니다."""
    redis_client.delete(_key(progress_id))
