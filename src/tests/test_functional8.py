from fastapi.testclient import TestClient
from main import app  # import your FastAPI app

import pandas as pd
import uuid
import io

client = TestClient(app)

def test_upload_dataset_to_real_minio():
    # Create dummy DataFrame
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'age': [30, 25],
        'city': ['Athens', 'Thessaloniki']
    })

    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=';')
    csv_buffer.seek(0)

    # Set metadata
    disease = "AML"
    node = "test-node"
    filename = f"{disease}_{node}_{uuid.uuid4()}.csv"

    files = {
        "file": (filename, csv_buffer.getvalue(), "text/csv"),
    }

    data = {
        "node": node,
        "disease": disease
    }

    # POST to FastAPI endpoint
    #response = client.post("/dataset", data=data, files=files)
    response = client.post(
    f"/dataset?node={node}&disease={disease}",
    files=files
)
    print("🔁 Response Status:", response.status_code)
    print("📄 Response Body:", response.text)


    assert response.status_code == 200, response.text
    print("✅ File uploaded to MinIO via FastAPI endpoint")
