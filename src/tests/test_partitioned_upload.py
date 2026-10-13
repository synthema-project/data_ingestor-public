"""Authenticated ingestion uses one frozen configuration and independent partitions."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock
import asyncio
import httpx
import pytest


@pytest.fixture
def ingestion(monkeypatch):
    source = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(source))
    db = ModuleType('database')
    db.create_db_and_tables = lambda: None
    db.get_session = lambda: None
    monkeypatch.setitem(sys.modules, 'database', db)
    spec = importlib.util.spec_from_file_location('ingestion_under_test', source / 'main.py')
    main = importlib.util.module_from_spec(spec); spec.loader.exec_module(main)
    main.NODE_NAME = 'ICH'
    metadata = {'use_case': 'AML', 'variables': [{'name': 'age'}, {'name': 'outcome'}]}
    configuration = {'version': 'frozen-version', 'documents': {'metadata': metadata,
                     'evaluation': {'privacy_evaluation': {'known_attributes': ['age'], 'sensitive_attributes': ['outcome']}}}}
    outgoing = []
    def transport(request):
        outgoing.append(request)
        return httpx.Response(200, json=configuration if request.method == 'GET' else {'message': 'registered'})
    client_class = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, 'AsyncClient', lambda **kwargs: client_class(transport=httpx.MockTransport(transport), **kwargs))
    user = SimpleNamespace(has_role=lambda role: True, synthema_roles=['ICH:Admin'])
    async def authenticated(): return user
    main.app.dependency_overrides[main.require_authentication] = authenticated
    objects = {}
    monkeypatch.setattr(main, 'save_dataframe_to_minio', lambda frame, key: objects.__setitem__(key, frame.copy()))
    monkeypatch.setattr(main, 'save_bytes_to_minio', lambda data, key, content_type: objects.__setitem__(key, data))
    return main, user, outgoing, objects, client_class


def upload(ingestion, path='/dataset', fields=None, authorized=True):
    main, _, _, _, client_class = ingestion
    async def call():
        async with client_class(transport=httpx.ASGITransport(app=main.app), base_url='http://test') as client:
            return await client.post(path, headers={'Authorization': 'Bearer provider-token'} if authorized else {},
                data={'use_case': 'AML', 'metadata': '{}', **(fields or {})},
                files={'file': ('data.csv', 'age,outcome\n1,0\n2,1\n3,0\n4,1\n5,0\n6,1\n7,0\n8,1\n9,0\n10,1\n', 'text/csv')})
    return asyncio.run(call())


@pytest.mark.parametrize("path", ["/dataset", "/dataset/partitioned"])
def test_versioned_upload_has_disjoint_partitions_and_forwarded_authentication(ingestion, path):
    response = upload(ingestion, path=path, fields={'configuration_version': 'frozen-version'})
    assert response.status_code == 200, response.text
    _, _, outgoing, objects, _ = ingestion
    frames = [frame for frame in objects.values() if hasattr(frame, 'columns')]
    assert sorted(len(frame) for frame in frames) == [2, 8]
    sets = [set(frame.age) for frame in frames]
    assert not sets[0] & sets[1]
    assert sets[0] | sets[1] == set(range(1, 11))
    assert list(frames[0].age) != list(range(1, 9))  # Shuffled, not a head/tail split.
    records = [json.loads(request.content) for request in outgoing if request.method == 'POST']
    assert {record['dataset_role'] for record in records} == {'train', 'test', 'schema'}
    assert {record['configuration_version'] for record in records} == {'frozen-version'}
    assert len({record['collection_id'] for record in records}) == 1
    assert all(request.headers['Authorization'] == 'Bearer provider-token' for request in outgoing)


def test_wrong_node_is_rejected_before_storage(ingestion):
    response = upload(ingestion, '/dataset/partitioned', {'node': 'UMCU'})
    assert response.status_code == 403
    assert not ingestion[3]


def test_nonmember_cannot_upload(ingestion):
    ingestion[1].has_role = lambda role: False
    ingestion[1].synthema_roles = ['UMCU:DataProvider']
    assert upload(ingestion).status_code == 403
    assert not ingestion[2]


def test_default_upload_still_requires_published_configuration(ingestion, monkeypatch):
    main, _, _, objects, client_class = ingestion
    monkeypatch.setattr(main.httpx, 'AsyncClient', lambda **kwargs: client_class(
        transport=httpx.MockTransport(lambda request: httpx.Response(404)), **kwargs))
    response = upload(ingestion)
    assert response.status_code == 422
    assert response.json()['detail'] == 'Publish a valid central metadata/evaluation configuration before uploading data'
    assert not objects


def test_two_row_split_is_nonempty_and_reproducible(ingestion):
    import pandas as pd
    main = ingestion[0]
    source = pd.DataFrame({'id': [1, 2]})
    partitions = main._split_train_test(source)
    assert set(partitions) == {'train', 'test'}
    assert [len(frame) for frame in partitions.values()] == [1, 1]
    assert source.id.tolist() == [1, 2]
    for role, frame in partitions.items():
        pd.testing.assert_frame_equal(frame, main._split_train_test(source)[role])
