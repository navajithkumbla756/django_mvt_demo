import requests

# Port 80 is served by Nginx / Gunicorn locally
BASE_URL = "http://127.0.0.1/api"

print("1. Authenticating recruiter...")
login_payload = {
    "email": "employer@example.com",
    "password": "Password@123"
}

try:
    login_res = requests.post(f"{BASE_URL}/auth/token/", json=login_payload)
    login_res.raise_for_status()
    tokens = login_res.json()
    access_token = tokens["access"]
    print(" Authentication successful! JWT Token acquired.")
except Exception as e:
    print(f" Login failed: {e}")
    if 'login_res' in locals():
        print("Response text:", login_res.text)
    exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

# 2. Fetch Pre-signed S3 Resume Link (Application ID 1)
print("\n2. Requesting Pre-signed S3 Download URL for Application #1...")
doc_res = requests.get(f"{BASE_URL}/resumes/1/download-url/", headers=headers)

print(f"Status Code: {doc_res.status_code}")
if doc_res.status_code == 200:
    data = doc_res.json()
    print(" S3 Pre-signed URL generated successfully:")
    print("Download URL:", data.get("download_url"))
    print("Expires in:", data.get("expires_in"), "seconds")
elif doc_res.status_code == 429:
    print(" Rate limited. Retry-After header:", doc_res.headers.get("Retry-After"))
else:
    print(" Error response:", doc_res.text)

# 3. Verify Analytics Funnel Endpoint
print("\n3. Testing Analytics Funnel endpoint...")
funnel_res = requests.get(f"{BASE_URL}/analytics/funnel/", headers=headers)
print(f"Funnel Status Code: {funnel_res.status_code}")
if funnel_res.status_code == 200:
    print(" Funnel Metrics Payload:", funnel_res.json())
else:
    print(" Funnel response:", funnel_res.text)
