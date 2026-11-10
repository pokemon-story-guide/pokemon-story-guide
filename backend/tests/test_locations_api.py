import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class LocationApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Small, independent fixtures keep HTTP behavior separate from production data.
        self.places = [{"id": 10, "name": "출현 장소"}, {"id": 20, "name": "빈 장소"}]
        self.pokemon = [
            {"id": 1, "name": "주리비얀", "types": ["grass"], "location_ids": [10]},
            {"id": 2, "name": "뚜꾸리", "types": ["fire"], "location_ids": None},
        ]
        loader = patch("api.services.location_service._load_json", side_effect={
            "place.json": self.places, "mon.json": self.pokemon,
        }.__getitem__)
        loader.start()
        self.addCleanup(loader.stop)
        self.addCleanup(self.client.close)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_locations(self):
        response = self.client.get("/api/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.places)

    def test_encounters_exclude_other_pokemon_and_internal_fields(self):
        response = self.client.get("/api/locations/10/pokemon")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 1, "name": "주리비얀", "types": ["grass"]}])

    def test_existing_empty_location(self):
        response = self.client.get("/api/locations/20/pokemon")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_unknown_location(self):
        response = self.client.get("/api/locations/999/pokemon")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 장소입니다.")

    def test_non_numeric_location(self):
        self.assertEqual(self.client.get("/api/locations/not-a-number/pokemon").status_code, 422)
