import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.services import trainer_service


class TrainerApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 1, "name": "예시 포켓몬 1", "types": ["fire"]},
            {"id": 2, "name": "예시 포켓몬 2", "types": ["ghost", "fire"]},
            {"id": 3, "name": "예시 포켓몬 3", "types": ["dragon"]},
        ]
        pokemon_loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        pokemon_loader.start()
        self.addCleanup(pokemon_loader.stop)
        self.trainers = [
            {"id": "leader-a", "name": "예시 관장", "category": "gym-leader", "type": "fire",
             "badge_order": 1, "image": "", "party": [{"pokemon_id": 1, "level": 10}]},
            {"id": "elite-a", "name": "예시 사천왕", "category": "elite-four", "type": "ghost",
             "image": "", "party": [{"pokemon_id": 2, "level": 50}]},
            {"id": "champion-a", "name": "예시 챔피언", "category": "champion", "type": None,
             "image": "", "party": [{"pokemon_id": 1, "level": 70}]},
            {"id": "plasma-a", "name": "예시 플라스마단", "category": "plasma", "type": None,
             "image": "", "party": [{"pokemon_id": 3, "level": 20}]},
        ]
        loader = patch("api.services.trainer_service._load_data", return_value=self.trainers)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def test_list_returns_all_without_party(self):
        response = self.client.get("/api/trainers")
        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([row["id"] for row in rows], ["leader-a", "elite-a", "champion-a", "plasma-a"])
        self.assertTrue(all("party" not in row for row in rows))

    def test_category_filter(self):
        cases = {"gym-leader": ["leader-a"], "elite-four": ["elite-a"], "champion": ["champion-a"], "plasma": ["plasma-a"],}
        for category, expected in cases.items():
            with self.subTest(category=category):
                response = self.client.get("/api/trainers", params={"category": category})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row["id"] for row in response.json()], expected)

    def test_invalid_category_returns_422_before_loading_data(self):
        response = self.client.get("/api/trainers", params={"category": "river"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["query", "category"])
        self.loader.assert_not_called()

    def test_detail_includes_party_and_null_badge_order(self):
        response = self.client.get("/api/trainers/elite-a")
        self.assertEqual(response.status_code, 200)
        row = response.json()
        expected = [
            {"pokemon_id": 2, "name": "예시 포켓몬 2", "types": ["ghost", "fire"],
             "level": 50, "image": None},
        ]
        self.assertEqual(row["party"], expected)
        self.assertIsNone(row["badge_order"])

    def test_party_with_unknown_pokemon_returns_500(self):
        self.trainers[0]["party"] = [{"pokemon_id": 999, "level": 10}]
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/trainers/leader-a")
        self.assertEqual(response.status_code, 500)

    def test_every_listed_id_has_detail(self):
        ids = [row["id"] for row in self.client.get("/api/trainers").json()]
        for trainer_id in ids:
            with self.subTest(trainer_id=trainer_id):
                response = self.client.get(f"/api/trainers/{trainer_id}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["id"], trainer_id)

    def test_unknown_id_returns_404(self):
        response = self.client.get("/api/trainers/nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 인물입니다.")


class TrainerDataFolderTest(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.data_dir = Path(temp_dir.name)
        data_dir = patch("api.services.trainer_service.DATA_DIR", self.data_dir)
        data_dir.start()
        self.addCleanup(data_dir.stop)

    def test_missing_folder_raises_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "폴더가 없습니다"):
            trainer_service._load_data()

    def test_empty_folder_raises_error(self):
        for folder in trainer_service.CATEGORY_DIRS:
            (self.data_dir / folder).mkdir()
        with self.assertRaisesRegex(FileNotFoundError, "비어 있습니다"):
            trainer_service._load_data()

    def test_missing_folder_returns_500_not_empty_list(self):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/trainers")
        self.assertEqual(response.status_code, 500)