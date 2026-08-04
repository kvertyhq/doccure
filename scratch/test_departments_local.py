import urllib.request
import urllib.error
import json

# Login locally
login_url = "http://127.0.0.1:8004/api/v1/auth/login"
data = json.dumps({
    'email': 'aditya.trivedi@example.com',
    'password': 'password123'
}).encode()

req = urllib.request.Request(
    login_url,
    data=data,
    headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
)

try:
    with urllib.request.urlopen(req) as response:
        login_res = json.loads(response.read().decode())
        token = login_res['data']['token']
        print("Local Login Success, Token:", token)
except Exception as e:
    print("Local Login failed:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
    exit(1)

# Get departments locally
departments_url = "http://127.0.0.1:8004/api/v1/departments"
req2 = urllib.request.Request(
    departments_url,
    headers={
        'Authorization': f'Bearer {token}',
        'User-Agent': 'Mozilla/5.0'
    }
)

try:
    with urllib.request.urlopen(req2) as response:
        print("\nLocal Departments API Success:")
        print(json.dumps(json.loads(response.read().decode()), indent=2))
except urllib.error.HTTPError as e:
    print(f"\nLocal Departments API HTTP Error {e.code}:")
    print(e.read().decode())
except Exception as e:
    print("\nLocal Departments API Error:", e)
