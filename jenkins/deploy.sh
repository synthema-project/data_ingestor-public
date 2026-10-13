#!/usr/bin/env bash
# Run from the repository root. Jenkins exports K8S_NAMESPACE and DOCKER_TAG.
set -euo pipefail
: "${K8S_NAMESPACE:?Set the existing target namespace}"
: "${DOCKER_TAG:?Set the image tag published by Jenkins}"
[[ "$K8S_NAMESPACE" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ && ${#K8S_NAMESPACE} -le 63 ]] || {
  echo 'Invalid Kubernetes namespace' >&2; exit 2;
}
[[ "$DOCKER_TAG" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$ ]] || {
  echo 'Invalid Docker tag' >&2; exit 2;
}
rendered=$(mktemp)
trap 'rm -f -- "$rendered"' EXIT
sed "s/DOCKER_TAG/$DOCKER_TAG/g" k8s/manifest.yml > "$rendered"
# Configuration must exist in the same namespace before pods start.
bash jenkins/apply-secret.sh
kubectl --namespace "$K8S_NAMESPACE" apply -f k8s/configmap.yml
kubectl --namespace "$K8S_NAMESPACE" apply -f "$rendered"
kubectl --namespace "$K8S_NAMESPACE" rollout status deployment/data-ingestor --timeout=180s
