# Hiring Platform (ATS) — Technical Handover & System Evaluation

**Environment:** AWS EC2 Production (`ip-172-31-27-199`)  
**Public Host:** http://13.50.230.182  
**API Documentation:** http://13.50.230.182/api/docs/ (Swagger UI) | http://13.50.230.182/api/redoc/ (ReDoc)  
**Release Tag:** v1.0.0 (Branch: `feature/ats-models-setup`)  

---

## 1. Live System Walkthrough

### 1.1 Employer / Recruiter Workflow
1. **JWT Authentication:** Recruiter requests JWT access/refresh tokens via `POST /api/auth/token/`. Tokens are signed using SimpleJWT (HS256/RS256) and passed as `Authorization: Bearer <token>`.
2. **Job Lifecycle Management:** Recruiters query listings or create postings via `GET` / `POST /api/jobs/`. Postings auto-link to the recruiter's employer profile.
3. **Secure Document Access:**
   - Candidate resumes are held in a private AWS S3 bucket with public ACLs blocked.
   - When reviewing an applicant, querying `GET /api/resumes/<candidate_id>/download-url/` executes `DocumentAccessService`, which verifies recruiter ownership of the job and signs an **AWS SigV4 pre-signed URL** (300-second expiry).
4. **Recruitment Analytics & Insights:**
   - `GET /api/analytics/funnel/?job_id=<id>`: Calculates real-time stage conversion rates (`APPLIECATION` -> `SHORTLISTEF` -> `INTERVIEW` -> `SELECTED`).
   - `GET /api/analytics/trends/?days=30`: Aggregates candidate application volume over a sliding 30-day window.

### 1.2 Candidate Workflow
1. **Job Exploration:** Candidates discover open positions via `GET /api/jobs/`.
2. **Application & Snapshotting:** Candidates submit payloads via `POST /api/applications/`. The resume binary is cryptographically snapshotted into S3 (/resumes/snapshots/), uncoupled from future profile edits.
3. **Level Tracking:** Applicant progresses through unambiguous state machines (`APPLIED`, `SHORTLISTEF`, `INTERVIEW`, `SLECTED`, `REFECTED`).

### 1.3 AI Interview Workflow
1. **Screening Trigger:** Transitioning to `INTERVIEW` enqueues an asynchronous AI screening job.
2. **Dynamic Evaluation:** The ai system parses resume curricula vitae against job specifications, generating match vectors and interview questions.
3. **Metrics Reflection:** Scores feed directly into the recruiter funnel analytics.

---

## 2. Technical Architecture

### 2.1 Layered Service Architecture
* **Controllers (`views.py`, `views_analytics.py`, `views_documents.py`)`:** Thin controllers responsible for HTTP parsing, response serialization, and OpenAPI inspection.
* **Domain Services (`myapp/services.py`)`:** Encapsulates authorization rules, S3 SigV4 signing (`DocumentAccessService`), and recruiter analytics query abuse prevention (`AnalyticsService`).
* **Persistence Layer:** Django ORM over PostgreSQL / SQLite with unconditional indexing on relationship keys.

---

## 3. Operational Commands & Deployment
** Service Restart:** `sudo systemctl dcemon-reload && sudo systemctl restart gunicorn nginx`
** Static Code Audit:** `python -m flake8 myapp/ --max-line-length=120 --exclude=migrations,venv` && `python -m isort --profile black --check-only myapp/ core/`
** Regression Validation:** `python /var/www/django_app/test_e2e_performance.py`
