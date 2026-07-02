import json
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8000"

endpoints = [
    ("GET", "/health", None),
    ("GET", "/api/system", None),
    ("POST", "/api/chat", {"message": "Hello"}),
    ("POST", "/api/chat/stream", {"message": "Hello"}),
    ("GET", "/api/memory", None),
    ("GET", "/api/history", None),
    ("POST", "/api/automation", {"goal": "test", "steps": [], "expected_output": "test"}),
    ("GET", "/api/automation/history", None),
    ("POST", "/api/browser", {"action": "navigate", "url": "https://example.com"}),
    ("POST", "/api/voice", {"action": "stop_listening"}),
]

results = []

for method, path, body in endpoints:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)

    if body is not None:
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(body).encode('utf-8')
        req.data = data

    try:
        response = urllib.request.urlopen(req)
        status = response.getcode()
        body_resp = response.read().decode('utf-8')
        results.append({"path": path, "status": status, "error": None})
        print(f"OK {method} {path} - {status}")
    except urllib.error.HTTPError as e:
        body_resp = e.read().decode('utf-8')
        results.append({"path": path, "status": e.code, "error": body_resp})
        print(f"FAIL {method} {path} - {e.code} - {body_resp}")
    except Exception as e:
        results.append({"path": path, "status": 0, "error": str(e)})
        print(f"FAIL {method} {path} - Exception: {str(e)}")

with open("test_results.json", "w") as f:
    json.dump(results, f)
