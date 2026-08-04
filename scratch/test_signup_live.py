import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/v1/auth/signup"
data = json.dumps({
    "email": "testuser_live@example.com",
    "password": "mySecurePassword123"
}).encode('utf-8')

req = urllib.request.Request(
    url,
    data=data,
    headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print("STATUS CODE:", response.status)
        print("RESPONSE BODY:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print("ERROR:", e)
