# tests/func.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from utils import save_dataframe_to_minio, remove_dataset_from_minio


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_external_systems():
    with patch("main.save_dataframe_to_minio", return_value="uploaded.csv"), \
         patch("main.remove_dataset_from_minio", return_value=True), \
         patch("main.get_dataset_from_minio", return_value=pd.DataFrame({"a":[1],"b":[2]})), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_post.return_value.status_code = 200
        mock_post.return_value.json = lambda: {}

        yield


def test_full_ingestion_flow_functional():
    # Upload
    upload = client.post(
        "/dataset",
        files={"file": ("test.csv", b"123", "text/csv")},
        data={"use_case": "aml1", "node": "NODE1"}
    )
    assert upload.status_code == 200

    # Delete
    delete = client.delete("/dataset", params={"filename": "uploaded.csv"})
    assert delete.status_code == 200
