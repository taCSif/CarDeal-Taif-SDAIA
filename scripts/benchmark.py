from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
start = time.perf_counter()
subprocess.run(["python", "-m", "pytest", "-q"], cwd=root, check=True)
test_seconds = round(time.perf_counter() - start, 3)
sha = subprocess.check_output(
    ["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True
).strip()
image = subprocess.run(
    ["docker", "images", f"saudi-used-car-deal-checker:{sha}", "--format", "{{.Size}}"],
    cwd=root, text=True, capture_output=True,
)
result = {
    "test_suite_seconds": test_seconds,
    "docker_image_size": image.stdout.strip() or "NOT_BUILT",
}
Path("artifacts/benchmarks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
