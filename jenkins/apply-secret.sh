#!/usr/bin/env bash
# Jenkins exports build parameters as environment variables. Do not trace secrets.
set +x
set -euo pipefail
: "${K8S_NAMESPACE:?Set the target namespace}"
[[ "$K8S_NAMESPACE" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ && ${#K8S_NAMESPACE} -le 63 ]] || {
  echo 'Invalid Kubernetes namespace' >&2; exit 2;
}
for input in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD MINIO_ACCESS_KEY MINIO_SECRET_KEY; do
  if [[ -z "${!input:-}" ]]; then
    echo "Missing required Jenkins input: $input" >&2
    exit 2
  fi
done

# Read values from the environment, preserving special characters and newlines.
# Stream directly to kubectl: no secret file or secret values in command arguments.
python3 - <<'PY' | kubectl --namespace "$K8S_NAMESPACE" apply -f -
import json
import os

keys = (
    'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
    'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY',
    'CATALOGUE_TOKEN',
)
print(json.dumps({
    'apiVersion': 'v1',
    'kind': 'Secret',
    'metadata': {
        'name': 'minio-secret',
        'namespace': os.environ['K8S_NAMESPACE'],
    },
    'type': 'Opaque',
    'stringData': {key: os.environ.get(key, '') for key in keys},
}))
PY
