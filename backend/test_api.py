import requests
import json

BASE = "http://localhost:5000/api"
results = []


def check(name, method, url, body=None, expect_keys=None, expect_status=200):
    try:
        r = requests.request(method, url, json=body, timeout=5)
        data = r.json()
        ok = r.status_code == expect_status
        missing = [k for k in (expect_keys or []) if k not in data]
        passed = ok and not missing
        detail = f"status={r.status_code}"
        if missing:
            detail += f" | missing_keys={missing}"
        if not ok:
            detail += f" | body={json.dumps(data)[:120]}"
        results.append((passed, name, detail))
    except Exception as e:
        results.append((False, name, str(e)))


check(
    "GET /health",
    "GET", f"{BASE}/health",
    expect_keys=["status", "gemini", "features", "global_avg_cycle"],
)

check(
    "POST /predict - normal (with history)",
    "POST", f"{BASE}/predict",
    {"age": 23, "cycle_length": 28, "cycle_number": 5, "history": [27, 29, 28, 30]},
    ["success", "prediction", "disclaimer"],
)

check(
    "POST /predict - cold start (no history)",
    "POST", f"{BASE}/predict",
    {"age": 18, "cycle_length": 30},
    ["success", "prediction"],
)

check(
    "POST /predict - short irregular cycle",
    "POST", f"{BASE}/predict",
    {"age": 22, "cycle_length": 16, "history": [17, 15]},
    ["success", "prediction"],
)

check(
    "POST /predict - long cycle",
    "POST", f"{BASE}/predict",
    {"age": 25, "cycle_length": 42, "history": [40, 44, 41]},
    ["success", "prediction"],
)

check(
    "POST /predict - missing 'age' returns 400",
    "POST", f"{BASE}/predict",
    {"cycle_length": 28},
    ["error"],
    expect_status=400,
)

check(
    "POST /predict - missing 'cycle_length' returns 400",
    "POST", f"{BASE}/predict",
    {"age": 22},
    ["error"],
    expect_status=400,
)

check(
    "POST /predict - prediction keys present",
    "POST", f"{BASE}/predict",
    {"age": 23, "cycle_length": 28, "history": [27, 29]},
    None,
)

# Verify prediction sub-keys
try:
    r = requests.post(f"{BASE}/predict", json={"age": 23, "cycle_length": 28, "history": [27, 29]}, timeout=5)
    pred = r.json().get("prediction", {})
    required_pred_keys = ["label", "confidence_pct", "lower_bound", "upper_bound", "predicted", "message", "consult"]
    missing = [k for k in required_pred_keys if k not in pred]
    in_range = 15 <= pred.get("predicted", 0) <= 60
    passed = not missing and in_range
    detail = f"keys_ok={not missing}, predicted_in_range={in_range}"
    if missing:
        detail += f", missing={missing}"
    results.append((passed, "POST /predict - prediction body structure", detail))
except Exception as e:
    results.append((False, "POST /predict - prediction body structure", str(e)))

check(
    "POST /chat - 'kram' keyword triggers KB",
    "POST", f"{BASE}/chat",
    {"message": "Kram perut sangat sakit saat haid"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - 'telat' keyword",
    "POST", f"{BASE}/chat",
    {"message": "Siklus haid saya telat sudah 2 minggu"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - 'mood' keyword",
    "POST", f"{BASE}/chat",
    {"message": "Mood saya jelek sekali sebelum haid"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - 'darah' keyword",
    "POST", f"{BASE}/chat",
    {"message": "Darah haid saya sangat banyak"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - 'keputihan' keyword",
    "POST", f"{BASE}/chat",
    {"message": "Keputihan saya berwarna kuning"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - unknown topic (fallback)",
    "POST", f"{BASE}/chat",
    {"message": "Apa itu endometriosis?"},
    ["success", "reply", "mode"],
)

check(
    "POST /chat - empty message returns 400",
    "POST", f"{BASE}/chat",
    {"message": ""},
    ["error"],
    expect_status=400,
)

check(
    "GET /symptoms",
    "GET", f"{BASE}/symptoms",
    expect_keys=["keywords", "topics"],
)

# Verify /symptoms content
try:
    r = requests.get(f"{BASE}/symptoms", timeout=5)
    data = r.json()
    expected_kw = {"kram", "mood", "telat", "darah", "keputihan"}
    actual_kw = set(data.get("keywords", []))
    missing_kw = expected_kw - actual_kw
    passed = not missing_kw
    results.append((passed, "GET /symptoms - all 5 keywords present",
                     f"ok" if passed else f"missing={missing_kw}"))
except Exception as e:
    results.append((False, "GET /symptoms - all 5 keywords present", str(e)))


# Print results
print()
passed_count = sum(1 for r in results if r[0])
failed_count = sum(1 for r in results if not r[0])

for ok, name, detail in results:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}")
    if not ok:
        print(f"         => {detail}")

print()
print(f"  {'='*50}")
print(f"  Results: {passed_count} passed / {failed_count} failed / {len(results)} total")
print(f"  {'='*50}")

if failed_count > 0:
    exit(1)
