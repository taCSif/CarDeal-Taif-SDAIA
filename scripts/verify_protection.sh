#!/usr/bin/env bash
# Verify main's branch protection actually matches what README.md documents.
# Requires: gh (authenticated) — uses `gh api --jq`, which bundles its own jq
# engine, so no separate jq install is required. Exits non-zero and prints
# the gap if protection is missing or weaker than expected; never modifies
# anything.
set -euo pipefail

REPO="${REPO:-taCSif/CarDeal-Taif-SDAIA}"
ENDPOINT="repos/${REPO}/branches/main/protection"
REQUIRED_CONTEXTS=("quality" "docker" "publish")

if ! gh api "$ENDPOINT" >/dev/null 2>/tmp/verify_protection_err; then
  echo "FAIL: branch protection is not enabled on ${REPO}#main" >&2
  cat /tmp/verify_protection_err >&2
  exit 1
fi

fail=0

for ctx in "${REQUIRED_CONTEXTS[@]}"; do
  if ! gh api "$ENDPOINT" --jq ".required_status_checks.contexts | index(\"$ctx\") != null" \
      | grep -q true; then
    echo "FAIL: required status check '$ctx' is not enforced" >&2
    fail=1
  fi
done

check_bool() {
  local jq_expr="$1" message="$2"
  if ! gh api "$ENDPOINT" --jq "$jq_expr" | grep -q true; then
    echo "FAIL: $message" >&2
    fail=1
  fi
}

check_bool '.required_status_checks.strict == true' \
  "required_status_checks.strict is not true (branch must be up to date before merge)"
check_bool '.allow_force_pushes.enabled == false' \
  "force pushes to main are not disabled"
check_bool '.allow_deletions.enabled == false' \
  "branch deletion is not disabled"

if [ "$fail" -ne 0 ]; then
  echo "Branch protection exists but does not meet the documented minimum. See README.md 'Branch protection'." >&2
  exit 1
fi

echo "OK: main is protected — required checks (${REQUIRED_CONTEXTS[*]}), strict, no force-push, no deletion."
