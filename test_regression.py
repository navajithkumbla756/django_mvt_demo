import requests

BASE_URL = "http://127.0.0.1/api"

print("========================================")
print("  PRODUCTION REGRESSION TEST SUITE     ")
print("========================================")

# 1. Test Recruiter JWT Authentication
print("\n[Test 1] Recruiter Authentication...")
auth_res = requests.post(f"{BASE_URL}/auth/token/", json={
    "email": "employer@example.com",
    "password": "Password@123"
})
assert auth_res.status_code == 200, f"Auth failed: {auth_res.text}"
token = auth_res.json()["access"]
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
print(" PASS: JWT Token obtained.")

# 2. Test Invalid Credentials (Negative Regression)
print("\n[Test 2] Invalid Credentials Rejection...")
bad_auth = requests.post(f"{BASE_URL}/auth/token/", json={
    "email": "employer@example.com",
    "password": "WrongPassword999"
})
assert bad_auth.status_code == 401, f"Expected 401, got {bad_auth.status_code}"
print(" PASS: 401 Unauthorized returned for bad credentials.")

# 3. Test Jobs List Endpoint
print("\n[Test 3] Job Dashboard Retrieval...")
jobs_res = requests.get(f"{BASE_URL}/jobs/", headers=headers)
assert jobs_res.status_code in [200, 204], f"Jobs endpoint failed: {jobs_res.text}"
print(" PASS: Jobs retrieved successfully.")

# 4. Test S3 Pre-Signed Resume Generation
print("\n[Test 4] S3 Pre-signed Resume Download...")
resume_res = requests.get(f"{BASE_URL}/resumes/1/download-url/", headers=headers)
assert resume_res.status_code == 200, f"Resume endpoint failed: {resume_res.text}"
resume_data = resume_res.json()
assert "download_url" in resume_data and "expires_in" in resume_data
print(" PASS: SigV4 download URL generated successfully.")

# 5. Test Non-existent Resume (404 Handling)
print("\n[Test 5] Non-existent Application (404 Not Found)...")
missing_res = requests.get(f"{BASE_URL}/resumes/999999/download-url/", headers=headers)
assert missing_res.status_code == 404, f"Expected 404, got {missing_res.status_code}"
print(" PASS: 404 Not Found handled gracefully.")

# 6. Test Recruiter Analytics Funnel
print("\n[Test 6] Recruiter Funnel Analytics...")
funnel_res = requests.get(f"{BASE_URL}/analytics/funnel/", headers=headers)
assert funnel_res.status_code == 200, f"Funnel failed: {funnel_res.text}"
assert "funnel" in funnel_res.json()
print(" PASS: Conversion funnel calculated successfully.")

# 7. Test Recruiter Analytics Trends
print("\n[Test 7] Candidate Sourcing Trends...")
trends_res = requests.get(f"{BASE_URL}/analytics/trends/?days=30", headers=headers)
assert trends_res.status_code == 200, f"Trends failed: {trends_res.text}"
assert "trends" in trends_res.json()
print(" PASS: Candidate trends sliding window verified.")

# 8. Test OpenAPI Documentation Availability
print("\n[Test 8] Swagger Schema Endpoints...")
schema_res = requests.get("http://127.0.0.1/api/schema/")
docs_res = requests.get("http://127.0.0.1/api/docs/")
assert schema_res.status_code == 200 and docs_res.status_code == 200
print(" PASS: Swagger UI and OpenAPI schema reachable.")

print("\n========================================")
print(" ALL 8 REGRESSION TESTS PASSED (0 ERRORS)")
print("========================================")
