#!/usr/bin/env bash
# Real measurements for BENCHMARKS.md, run from the repo root:
#   - docker image size (bytes) and top Docker layers by size
#   - wall time of `make fast-test` and `make test`
#
# Every number this script prints comes from an actual command run right
# here, not an assumption. Pass --skip-docker to only measure test timing
# (e.g. when Docker isn't available in this environment).
set -euo pipefail
cd "$(dirname "$0")/.."

SKIP_DOCKER=0
[ "${1:-}" = "--skip-docker" ] && SKIP_DOCKER=1

SHA="$(git rev-parse --short HEAD)"
IMAGE="saudi-used-car-deal-checker:${SHA}"

echo "== make fast-test =="
FAST_START=$(date +%s)
make fast-test
FAST_SECONDS=$(( $(date +%s) - FAST_START ))
echo "fast-test wall time: ${FAST_SECONDS}s"
echo

echo "== make test =="
TEST_START=$(date +%s)
make test
TEST_SECONDS=$(( $(date +%s) - TEST_START ))
echo "test wall time: ${TEST_SECONDS}s"
echo

IMAGE_SIZE_BYTES=""
BUILD_SECONDS=""
if [ "$SKIP_DOCKER" -eq 0 ]; then
  echo "== docker build =="
  test -f artifacts/price_model.joblib || make train
  BUILD_START=$(date +%s)
  docker build -t "$IMAGE" .
  BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))
  IMAGE_SIZE_BYTES="$(docker image inspect "$IMAGE" --format '{{.Size}}')"
  echo "build wall time: ${BUILD_SECONDS}s"
  echo "image size: ${IMAGE_SIZE_BYTES} bytes"
  echo
  echo "== docker history: top layers by size =="
  docker history --human=false --format '{{.Size}}\t{{.CreatedBy}}' "$IMAGE" \
    | sort -rh | head -10
  echo
else
  echo "== docker build skipped (--skip-docker) =="
  echo
fi

echo "== Summary =="
echo "fast-test: ${FAST_SECONDS}s (target: <= 60s)"
echo "test:      ${TEST_SECONDS}s"
if [ "$SKIP_DOCKER" -eq 0 ]; then
  MB=$(( IMAGE_SIZE_BYTES / 1000000 ))
  echo "build:     ${BUILD_SECONDS}s"
  echo "image:     ${IMAGE_SIZE_BYTES} bytes (~${MB} MB, target: <= 500 MB)"
fi
