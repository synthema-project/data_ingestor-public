import requests
import unittest

class TestDataIngestorAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8003"

    def test_save_dataset_info(self):
        data = {
            "node": "NODE1",
            "path": "/path/to/data",
            "disease": "DiseaseA"
        }
        response = requests.post(f"{self.BASE_URL}/metadata", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Metadata uploaded successfully", response.json().get("message", ""))

    def test_get_dataset_info(self):
        params = {"node": "NODE1", "disease": "DiseaseA"}
        response = requests.get(f"{self.BASE_URL}/metadata/{params['disease']}", params=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["node"], "NODE1")

    def test_remove_dataset_info(self):
        data = {
            "node": "NODE1",
            "path": "/path/to/data",
            "disease": "DiseaseA"
        }
        response = requests.delete(f"{self.BASE_URL}/metadata", params=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Dataset '/path/to/data' deleted successfully.", response.json().get("message", ""))

if __name__ == "__main__":
    unittest.main()
