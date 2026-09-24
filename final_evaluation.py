import subprocess
import time
import requests

BASE_URL = "http://127.0.0.1/api"
print("=" * 70)
print("       ATS PLATFORM — FINAL SYSTEM EVALUATION AUDIT        ")
print("=" * 70)

eval_results = []

def record(metric, standard, actual, passed):
    status = "PASSED" if passed else "FAILED"
    eval_results.append((metric, standard, actual, status))
    print(f"[{status}] {metric.ljust(30)} | Target: {standard.ljust(20)} | Result: {actual}")

# 1. CODE STANDARDS
f8_proc = subprocess.run(
    ["python", "-m", "flake8", "myapp/", "--max-line-length=120", "--exclude=migrations,venv"],
    capture_output=True, text=True
)
record("PEP8 Code Quality", "0 flake8 errors", f"{len(f8_proc.stdout.splitlines())} errors", f8_proc.returncode == 0)

isort_proc = subprocess.run(
    ["python", "-m", "isort", "--profile", "black", "--check-only", "myapp/", "core/"],
    capture_output=True, text=True
)
record("Import Alignment", "100% Black/isort", "Compliant" if isort_proc.returncode == 0 else "Unaligned", isort_proc.returncode == 0)

# 2. AUTHENTICATION
t0 = time.time()
auth_res = requests.post(f"{BASE_URL}/auth/token/", json={"email": "employer@example.com", "password": "Password@123"})
auth_ok = auth_res.status_code == 200
token = auth_res.json().get("access") if auth_ok else ""
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
record("Authentication Flow", "HTTP 200 & JWT", f"HTTP {auth_res.status_code}", auth_ok)

# 3. S3 SIGV4
t0 = time.time()
s3_res = requests.get(f"{BASE_URL}/resumes/1/download-url/", headers=headers)
s3_lat = (time.time() - t0) * 1000
s3_ok = s3_res.status_code == 200 and "X-Amz-Signature" in s3_res.json().get("download_url", "")
record("S3 SigV4 Pre-signed URLs", "SigV4 Token (300s TTL)", "Valid" if s3_ok else "Failed", s3_ok)

# 4. ANALYTICS FUNNEL
t0 = time.time()
funnel_res = requests.get(f"{BASE_URL}/analytics/funnel/", headers=headers)
funnel_lat = (time.time() - t0) * 1000
funnel_ok = funnel_res.status_code == 200 and "funnel" in funnel_res.json()
record("Recruiter Analytics", "Funnel JSON", "Calculated" if funnel_ok else "Error", funnel_ok)

# 5. SWAGGER DOCS
docs_res = requests.get("http://127.0.0.1/api/docs/")
record("Swagger Docs", "HTTP 200", f"HTTP {docs_res.status_code}", docs_res.status_code == 200)

print("=" * 70)
all_passed = all(v == "PASSED" for _, _, _, v in eval_results)
print(f"OVERALL PLATFORM VERDICT: {'ACCEPTED (PRODUCTION READY)' if all_passed else 'REVISE'}")
print("=" * 70)
