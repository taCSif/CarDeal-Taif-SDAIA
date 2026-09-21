import json
import os
import urllib.request

base = os.getenv("BASE_URL", "http://localhost:8000")

for path in ("/health", "/ready"):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        print(path, response.status, response.read().decode())

payload = {
    "make":"Toyota","type":"Camry","year":2021,"origin":"Saudi","color":"White",
    "options":"Full","engine_size":2.5,"fuel_type":"Gas","gear_type":"Automatic",
    "mileage":80000,"region":"Riyadh","asking_price":72000,
}
request = urllib.request.Request(
    base + "/v1/predict", data=json.dumps(payload).encode(),
    headers={"Content-Type":"application/json", "X-Trace-ID":"smoke-test"}, method="POST",
)
with urllib.request.urlopen(request, timeout=10) as response:
    print("/v1/predict", response.status, response.read().decode())
