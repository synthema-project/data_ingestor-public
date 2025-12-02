# tests/func.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_external_systems():
    with patch("services.minio_service.upload_dataset_to_minio", return_value="uploaded.csv"):
        with patch("services.minio_service.remove_dataset_from_minio", return_value=True):
            with patch("services.catalogue_service.notify_catalogue_dataset_added", return_value=True):
                with patch("services.catalogue_service.notify_catalogue_dataset_deleted", return_value=True):
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
