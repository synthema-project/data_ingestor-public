# tests/func.py
import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -----------------------------
# Fixtures
# -----------------------------

def test_upload_csv_from_file(monkeypatch):
    # Path to real CSV in repo
    file_path = "tests/example_data/AML_DATA_ES.csv"

    # Mock external calls
    async def fake_save(df, name):
        return f"{name}"

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)
    monkeypatch.setattr("utils.validate_data", lambda data, schema: None)
    monkeypatch.setattr("httpx.AsyncClient.post", lambda *a, **k: None)

    with open(file_path, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"use_case": "aml1", "metadata": "{}"}
        )

    assert r.status_code == 200
