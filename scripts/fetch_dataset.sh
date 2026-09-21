#!/usr/bin/env bash
# Fetch the public Saudi Arabia Used Cars dataset from Kaggle into data/raw/.
#
# The Kaggle download API requires authentication even for public datasets, so
# KAGGLE_USERNAME and KAGGLE_KEY must be set (in CI, provide them as repository
# secrets). Get them from https://www.kaggle.com/settings -> "Create New Token".
#
# Result: data/raw/saudi_used_cars.csv (the cleaned English listings file).
set -euo pipefail

DATASET="turkibintalib/saudi-arabia-used-cars-dataset"
DEST_DIR="data/raw"
TARGET="${DEST_DIR}/saudi_used_cars.csv"

if [[ -z "${KAGGLE_USERNAME:-}" || -z "${KAGGLE_KEY:-}" ]]; then
  echo "ERROR: KAGGLE_USERNAME and KAGGLE_KEY must be set to download the dataset." >&2
  echo "Provide them as CI secrets or export them locally." >&2
  exit 1
fi

mkdir -p "${DEST_DIR}"
tmp_zip="$(mktemp --suffix=.zip)"
trap 'rm -f "${tmp_zip}"' EXIT

curl -sSL --fail --retry 3 \
  -u "${KAGGLE_USERNAME}:${KAGGLE_KEY}" \
  "https://www.kaggle.com/api/v1/datasets/download/${DATASET}" \
  -o "${tmp_zip}"

unzip -o "${tmp_zip}" -d "${DEST_DIR}"
test -f "${DEST_DIR}/UsedCarsSA_Clean_EN.csv"
mv -f "${DEST_DIR}/UsedCarsSA_Clean_EN.csv" "${TARGET}"
echo "Dataset ready at ${TARGET} ($(wc -l < "${TARGET}") lines)."
