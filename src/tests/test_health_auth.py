"""Kubernetes health probes are public; dataset endpoints remain protected."""
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def test_health_probe_does_not_disable_dataset_authentication():
    spec = importlib.util.spec_from_file_location('ingestor_health_test', Path(__file__).resolve().parents[1] / 'main.py')
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
    # No lifespan: do not connect to PostgreSQL or MinIO.
    client = TestClient(main.app)
    assert client.get('/healthcheck').status_code == 200
    for method, path in [('GET', '/dataset'), ('POST', '/dataset'),
                         ('POST', '/dataset/partitioned'), ('DELETE', '/dataset')]:
        assert client.request(method, path).status_code in (401, 403)
