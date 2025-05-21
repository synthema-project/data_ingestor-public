# tests/test_functional_upload.py

import pandas as pd
import requests
import io
import uuid
import logging

logging.basicConfig(level=logging.INFO)

def test_upload_dataset_endpoint():
    # Prepare a test DataFrame
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'age': [30, 25],
        'city': ['Athens', 'Thessaloniki']
    })

    # Convert DataFrame to CSV bytes
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=';')
    csv_buffer.seek(0)

    # Create a test filename and metadata
    disease = "test-disease"
    node = f"test-node"
    filename = f"{disease}_{node}_{uuid.uuid4()}.csv"

    # Compose the POST request
    files = {
        "file": (filename, csv_buffer.getvalue(), "text/csv"),
    }
    data = {
        "node": node,
        "disease": disease
    }

    # Change this URL to match your real endpoint
    #url = "http://localhost:82/dataset"  # or your staging IP:PORT
    #url = "data-ingestor.k8s.synthema.rid-intrasoft.eu:82"
    #url = "http://data-ingestor.k8s.synthema.rid-intrasoft.eu:82/dataset"
    url = "http://10.109.218.9:82/dataset"
    # Send the request
    logging.info(f"Uploading dataset to {url}")
    response = requests.post(url, data=data, files=files)

    # Check result
    logging.info(f"Response status: {response.status_code}")
    logging.info(f"Response body: {response.text}")
    assert response.status_code == 200, "Upload failed"
    assert "successfully" in response.text.lower()
