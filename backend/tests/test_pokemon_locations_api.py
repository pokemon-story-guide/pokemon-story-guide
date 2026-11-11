import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class PokemonLocationsApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.pokemon = [
            {"id": 0, "name": "예시 다중 출현", "types": ["grass"], "location_ids": [2, 0]},
            {"id": 1, "name": "예시 미등록", "types": ["fire"], "location_ids": None},
            {"id": 2, "name": "예시 빈 목록", "types": ["water"], "location_ids": []},
        ]
        self.places = [
            {"id": 0, "name": "예시 장소 A", "internal_note": "비공개 필드"},
            {"id": 1, "name": "연결되지 않은 장소"},
            {"id": 2, "name": "예시 장소 B"},
        ]
        loader = patch("api.services.pokemon_service._load_pokemon", return_value=self.pokemon)
        self.pokemon_loader = loader.start()
        self.addCleanup(loader.stop)
        places = patch("api.services.pokemon_service.location_service.get_locations", return_value=self.places)
        self.places_loader = places.start()
        self.addCleanup(places.stop)

    def test_multiple_locations_use_shared_ids_names_and_source_order(self):
        response = self.client.get("/api/pokemon/0/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {"id": 2, "name": "예시 장소 B"}, {"id": 0, "name": "예시 장소 A"},
        ])

    def test_single_location(self):
        self.pokemon[0]["location_ids"] = [0]
        response = self.client.get("/api/pokemon/0/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 0, "name": "예시 장소 A"}])

    def test_null_location_ids_return_empty_array(self):
        response = self.client.get("/api/pokemon/1/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.places_loader.assert_not_called()

    def test_empty_location_ids_return_empty_array(self):
        response = self.client.get("/api/pokemon/2/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.places_loader.assert_not_called()

    def test_unknown_pokemon_returns_404(self):
        response = self.client.get("/api/pokemon/999/locations")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "존재하지 않는 포켓몬입니다.")
        self.places_loader.assert_not_called()

    def test_non_numeric_id_returns_422(self):
        response = self.client.get("/api/pokemon/not-a-number/locations")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["path", "pokemon_id"])
        self.pokemon_loader.assert_not_called()

    def test_broken_reference_is_not_silently_returned_as_partial_success(self):
        self.pokemon[0]["location_ids"] = [0, 999]
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/pokemon/0/locations")
        self.assertEqual(response.status_code, 500)

    def test_data_read_failure_is_not_reported_as_no_locations(self):
        self.pokemon_loader.side_effect = OSError("예시 파일 읽기 실패")
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/pokemon/0/locations")
        self.assertEqual(response.status_code, 500)

    def test_search_response_is_unchanged(self):
        response = self.client.get("/api/pokemon", params={"name": "예시 다중"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": 0, "name": "예시 다중 출현", "types": ["grass"], "image": None,
        }])
        self.places_loader.assert_not_called()
