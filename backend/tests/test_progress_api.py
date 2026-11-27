import json
import unittest
import uuid
from unittest.mock import patch

import redis
from fastapi.testclient import TestClient

from api.main import app
from api.services import progress_service

DEFAULT = {"version": None, "gym_unlocked": 1, "champion_unlocked": False, "n_story_cleared": 0}
VALID = {"version": "black", "gym_unlocked": 4, "champion_unlocked": False, "n_story_cleared": 2}


class FakeRedis:
    """진짜 Redis 대신 쓰는 가짜 저장소입니다. 딕셔너리로 get/set/delete만 흉내 냅니다."""

    def __init__(self):
        self.data = {}
        self.expire = {}
        # True로 바꾸면 Redis가 꺼진 것처럼 연결 오류를 냅니다.
        self.broken = False

    def _check(self):
        if self.broken:
            raise redis.ConnectionError("가짜 연결 오류")

    def get(self, key):
        self._check()
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self._check()
        self.data[key] = value
        self.expire[key] = ex

    def delete(self, key):
        self._check()
        self.data.pop(key, None)
        self.expire.pop(key, None)


class ProgressApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.redis = FakeRedis()
        fake = patch("api.services.progress_service.redis_client", self.redis)
        fake.start()
        self.addCleanup(fake.stop)

    def _cookie_header(self, progress_id):
        return {"Cookie": f"progress_id={progress_id}"}

    def test_first_get_returns_default_and_sets_cookie(self):
        response = self.client.get("/api/progress")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), DEFAULT)
        cookie = response.headers["set-cookie"]
        self.assertIn("progress_id=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)
        self.assertNotIn("Secure", cookie)
        # 조회만 했으므로 저장된 기록은 없습니다.
        self.assertEqual(self.redis.data, {})

    def test_valid_cookie_is_kept(self):
        progress_id = uuid.uuid4().hex
        response = self.client.get("/api/progress", headers=self._cookie_header(progress_id))
        self.assertEqual(response.cookies["progress_id"], progress_id)

    def test_invalid_cookie_gets_new_id(self):
        response = self.client.get("/api/progress", headers=self._cookie_header("not-a-valid-id"))
        new_id = response.cookies["progress_id"]
        self.assertNotEqual(new_id, "not-a-valid-id")
        self.assertEqual(len(new_id), 32)

    def test_put_then_get_returns_saved_progress(self):
        put = self.client.put("/api/progress", json=VALID)
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.json(), VALID)
        get = self.client.get("/api/progress")
        self.assertEqual(get.json(), VALID)

    def test_put_saves_json_with_ttl(self):
        self.client.put("/api/progress", json=VALID)
        key = f"progress:{self.client.cookies['progress_id']}"
        self.assertEqual(json.loads(self.redis.data[key]), VALID)
        self.assertEqual(self.redis.expire[key], progress_service.TTL_SECONDS)

    def test_put_fills_missing_fields_with_default(self):
        response = self.client.put("/api/progress", json={"gym_unlocked": 3})
        self.assertEqual(response.json(), {**DEFAULT, "gym_unlocked": 3})

    def test_other_browser_has_separate_progress(self):
        self.client.put("/api/progress", json=VALID)
        with TestClient(app) as other:
            response = other.get("/api/progress")
        self.assertEqual(response.json(), DEFAULT)

    def test_invalid_progress_returns_422_without_saving(self):
        cases = [
            {"gym_unlocked": 0},
            {"gym_unlocked": 9},
            {"n_story_cleared": 7},
            {"version": "red"},
            {"cleared_badges": [1, 2]},
        ]
        for body in cases:
            with self.subTest(body=body):
                response = self.client.put("/api/progress", json=body)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.redis.data, {})

    def test_delete_resets_progress(self):
        self.client.put("/api/progress", json=VALID)
        response = self.client.delete("/api/progress")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.redis.data, {})
        self.assertEqual(self.client.get("/api/progress").json(), DEFAULT)

    def test_old_format_record_returns_default(self):
        progress_id = uuid.uuid4().hex
        self.redis.data[f"progress:{progress_id}"] = json.dumps({"cleared_badges": [1, 2]})
        response = self.client.get("/api/progress", headers=self._cookie_header(progress_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), DEFAULT)

    def test_broken_json_record_returns_default(self):
        progress_id = uuid.uuid4().hex
        self.redis.data[f"progress:{progress_id}"] = "{not json"
        response = self.client.get("/api/progress", headers=self._cookie_header(progress_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), DEFAULT)

    def test_redis_error_returns_503(self):
        self.redis.broken = True
        requests = [
            ("GET", lambda: self.client.get("/api/progress")),
            ("PUT", lambda: self.client.put("/api/progress", json=VALID)),
            ("DELETE", lambda: self.client.delete("/api/progress")),
        ]
        for method, send in requests:
            with self.subTest(method=method):
                response = send()
                self.assertEqual(response.status_code, 503)
                self.assertIn("기록 저장소", response.json()["detail"])


    def test_patch_changes_only_sent_fields(self):
        self.client.put("/api/progress", json=VALID)
        response = self.client.patch("/api/progress", json={"gym_unlocked": 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**VALID, "gym_unlocked": 5})
        self.assertEqual(self.client.get("/api/progress").json(), {**VALID, "gym_unlocked": 5})

    def test_patch_without_record_starts_from_default(self):
        response = self.client.patch("/api/progress", json={"champion_unlocked": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**DEFAULT, "champion_unlocked": True})
        key = f"progress:{self.client.cookies['progress_id']}"
        self.assertEqual(json.loads(self.redis.data[key]), {**DEFAULT, "champion_unlocked": True})

    def test_patch_version_null_resets_version(self):
        self.client.put("/api/progress", json=VALID)
        response = self.client.patch("/api/progress", json={"version": None})
        self.assertEqual(response.json(), {**VALID, "version": None})

    def test_invalid_patch_returns_422_without_saving(self):
        cases = [
            {"gym_unlocked": None},
            {"gym_unlocked": 9},
            {"n_story_cleared": -1},
            {"version": "red"},
            {"cleared_badges": [1, 2]},
        ]
        for body in cases:
            with self.subTest(body=body):
                response = self.client.patch("/api/progress", json=body)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.redis.data, {})

    def test_patch_redis_error_returns_503(self):
        self.redis.broken = True
        response = self.client.patch("/api/progress", json={"gym_unlocked": 5})
        self.assertEqual(response.status_code, 503)
        self.assertIn("기록 저장소", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
