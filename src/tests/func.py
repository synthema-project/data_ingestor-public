# tests/func.py
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

def test_upload_csv(monkeypatch):

    async def fake_save(df, name):
        return "file.csv"

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)

    r = client.post(
        "/dataset",
        files={"file": ("test.csv", b"a;b\n1;2\n", "text/csv")},
        data={"use_case": "aml1"}
    )

    assert r.status_code == 200

