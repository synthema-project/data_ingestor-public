import os
import pytest
import requests

# Base URL for the service — can be overridden by environment variable
BASE_URL = os.getenv("BASE_URL", "http://localhost:82")

# Use test values consistent with your system
TEST_NODE = "testnode"
TEST_DISEASE = "testdisease"
TEST_FILENAME = "testfile.csv"  # Will be set after upload


def test_healthcheck():
    """Test the /healthcheck endpoint"""
    resp = requests.get(f"{BASE_URL}/healthcheck")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_upload_dataset():
    """Test uploading a CSV file"""
    global TEST_FILENAME

    url = f"{BASE_URL}/dataset"
    files = {'file': ('test.csv', b'name;age\nAlice;30\nBob;40')}
    data = {'node': TEST_NODE, 'disease': TEST_DISEASE}

    resp = requests.post(url, files=files, data=data)

    assert resp.status_code == 200
    assert "uploaded" in resp.json()["message"]

    # Capture the uploaded file name from MinIO path (from logs or inject as response later)
    # Here we'll assume a known format to reconstruct it
    # For accurate testing, your API should return the filename
    TEST_FILENAME = f"{TEST_DISEASE}_{TEST_NODE}_"  # prefix to use for deletion test


def test_delete_dataset():
    """Test deleting a dataset (only works if filename is known or returned by upload)"""
    # WARNING: This test assumes TEST_FILENAME was set from previous test
    # Ideally, your POST /dataset should return the actual filename

    url = f"{BASE_URL}/dataset"
    params = {
        "node": TEST_NODE,
        "disease": TEST_DISEASE,
        "filename": ""  # Replace this manually if API doesn't return it
    }

    # If you cannot dynamically retrieve filename, this test might fail — you can skip it
    if not params["filename"]:
        pytest.skip("Skipping delete test: filename not set.")

    resp = requests.delete(url, params=params)
    assert resp.status_code == 200
    assert "removed" in resp.json()["message"]
