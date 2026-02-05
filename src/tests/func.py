# tests/func.py
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ---------------------------------------------------
# Fixtures
# ---------------------------------------------------

@pytest.fixture
def real_csv_file(tmp_path):
    """
    Creates a real CSV compatible with your schema
    """
    df = pd.DataFrame({
        "ID": [1, 2],
        "WHO 2016": ["AML", "AML"],
        "WHO 2016 label": ["A", "B"],
        "KARYOTYPE": ["46,XX", "46,XY"],
        "complex": [0, 1],
        "ASXL1": [1, 0]
    })

    file_path = tmp_path / "dataset.csv"
    df.to_csv(file_path, sep=";", index=False)
    return file_path


@pytest.fixture
def valid_metadata():
    return {
        "title": "AML dataset",
        "description": "test dataset",
        "publisher": {
            "name": "Org",
            "url": "http://org",
            "mail": "mail@org.com",
            "type": "org",
            "note": "note"
        }
    }


# ---------------------------------------------------
# Monkeypatch external systems
# ---------------------------------------------------

@pytest.fixture(autouse=True)
def mock_external(monkeypatch):
    async def fake_save(df, name):
        return name

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)
    monkeypatch.setattr("utils.validate_data", lambda data, schema: None)
    monkeypatch.setattr("httpx.AsyncClient.post", lambda *a, **k: None)


# ---------------------------------------------------
# Tests
# ---------------------------------------------------

def test_upload_dataset(real_csv_file, valid_metadata):
    with open(real_csv_file, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("dataset.csv", f, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": str(valid_metadata)
            }
        )

    assert r.status_code == 200
    assert r.json()["path"] == "dataset.csv"
    assert r.json()["use_case"] == "aml1"


def test_upload_missing_file():
    r = client.post("/dataset", data={"use_case": "aml1"})
    assert r.status_code == 422


def test_upload_invalid_metadata(real_csv_file):
    with open(real_csv_file, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("dataset.csv", f, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": "not-json"
            }
        )

    assert r.status_code == 400
