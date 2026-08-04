import urllib.request
import urllib.error
import json

# Login
login_url = "https://doccure.kverty.com/api/v1/auth/login"
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
        print("Login Success, Token:", token)
except Exception as e:
    print("Login failed:", e)
    exit(1)

# Get departments
departments_url = "https://doccure.kverty.com/api/v1/departments"
req2 = urllib.request.Request(
    departments_url,
    headers={
        'Authorization': f'Bearer {token}',
        'User-Agent': 'Mozilla/5.0'
    }
)

try:
    with urllib.request.urlopen(req2) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:")
    print(e.read().decode())
except Exception as e:
    print("Error:", e)
