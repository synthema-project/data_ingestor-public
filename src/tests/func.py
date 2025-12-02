# tests/func.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from utils import save_dataframe_to_minio, remove_dataset_from_minio, get_dataset_from_minio
import pandas as pd


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_external_systems():
    with patch("main.upload_dataset_to_minio", return_value="uploaded.csv"):
        with patch("main.delete_from_minio", return_value=True):
            with patch("main.post_metadata", return_value=True):
                yield


def test_full_ingestion_flow_functional():
    upload = client.post(
        "/dataset",
        files={"file": ("test.csv", b"123", "text/csv")},
        data={"use_case": "aml1", "node": "NODE1"}
    )

    assert upload.status_code == 200
    assert upload.json()["filename"] == "uploaded.csv"

    delete = client.delete("/dataset", params={"filename": "uploaded.csv"})
    assert delete.status_code == 200
