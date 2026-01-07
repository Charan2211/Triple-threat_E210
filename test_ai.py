import requests
import json

# Test AI endpoints
endpoints = [
    "http://127.0.0.1:5000/api/ai/health",
    "http://127.0.0.1:5000/api/ai/recommend",
    "http://127.0.0.1:5000/api/ai/recommend?category=advertising&count=5",
    "http://127.0.0.1:5000/api/ai/categories"
]

for url in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")