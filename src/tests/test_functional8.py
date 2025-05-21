from fastapi.testclient import TestClient
from main import app  # import your FastAPI app

import pandas as pd
import uuid
import io

#client = TestClient(app)

#def test_upload_dataset_to_real_minio():
#    # Create dummy DataFrame
#    df = pd.DataFrame({
#        'name': ['Alice', 'Bob'],
#        'age': [30, 25],
#        'city': ['Athens', 'Thessaloniki']
#    })

#    # Convert to CSV
#    csv_buffer = io.StringIO()
#    df.to_csv(csv_buffer, index=False, sep=';')
#    csv_buffer.seek(0)

#    # Set metadata
#    disease = "AML"
#    node = "test-node"
#    filename = f"{disease}_{node}_{uuid.uuid4()}.csv"

#    files = {
#        "file": (filename, csv_buffer.getvalue(), "text/csv"),
#    }

#    data = {
#        "node": node,
#        "disease": disease
#    }

#    # POST to FastAPI endpoint
#    #response = client.post("/dataset", data=data, files=files)
#    response = client.post(
#    f"/dataset?node={node}&disease={disease}",
#    files=files
#)
#    print("🔁 Response Status:", response.status_code)
#    print("📄 Response Body:", response.text)


#    assert response.status_code == 200, response.text
#    print("✅ File uploaded to MinIO via FastAPI endpoint")

client = TestClient(app)

def test_upload_and_delete_dataset_from_minio():
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
    fixed_uuid = "d7976598-eb08-4d3a-b5ad-9481f6ad0db7"
    filename = f"{disease}_{node}_{fixed_uuid}.csv"
    #filename = f"{disease}_{node}_{uuid.uuid4()}.csv"

    # Upload the file
    files = {
        "file": (filename, csv_buffer.getvalue(), "text/csv"),
    }

    upload_response = client.post(
        f"/dataset?node={node}&disease={disease}",
        files=files
    )

    assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
    print("✅ Upload successful")

    # Delete the file
    #delete_response = client.delete(
    #    f"/dataset?node={node}&disease={disease}&filename={filename}"
    #)

    delete_response = client.delete(
        "/dataset",
        params={"node": node, "disease": disease, "filename": filename}
    )

    assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
    print("🗑️ Delete successful")

