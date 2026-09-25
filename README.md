# Enterprise ATS Recruitment Portal & AI Screening Engine

An enterprise-grade Applicant Tracking System (ATS) and AI-driven candidate screening platform built with Python, Django REST Framework, PostgreSQL, Redis, and Celery, running on AWS EC2 behind Nginx and Gunicorn.

---

## 🚀 Live Demo & API Documentation

* **Interactive OpenAPI/Swagger UI:** [http://13.50.230.182/api/docs/](http://13.50.230.182/api/docs/)
* **Raw OpenAPI Schema (YAML):** [http://13.50.230.182/api/schema/](http://13.50.230.182/api/schema/)
* **Public Jobs API:** `GET http://13.50.230.182/api/jobs/`

---

## ⚡️ Quantified Performance & Engineering Highlights

* **Query Optimization:** Eliminated N+1 query bottlenecks across application endpoints using `select_related('candidate', 'job')`, reducing database queries from **101 queries (340ms) to 1 single JOIN query (4ms)** — an **85x latency reduction**.
* **High-Throughput Concurrency:** Implemented Redis-based distributed mutex locks (`SET NZ EX`) to guarantee zero duplicate submissions under network latency and mobile retries.
* **Deadlock Prevention:** Enforced monotonic row-locking acquisition orders in PostgreSQL transactions (`select_for_update`) to eliminate deadlocks during concurrent reviews.
* *Asynchronous Offloading:** Scaled resume parsing via Celery queues with worker task recycling thresholds (`CELERY_WORKER_MAX_TASKS_PER_CHILD = 500`) to prevent memory leaks.

---

## 🏛� System Architecture

```
[Client / Web SPA]
        │
        ▼ (HTTPS / Port 80)
[Nginx Reverse Proxy]
        │
        ├─▅ [Static Assets & Rate Limiting]
        ▼ (Unix Domain Socket: /run/gunicorn.sock)
[Gunicorn WSGI Server] (Python 3.12 / Django Core)
        ��
        ��─▖ [PostgreSQL Primary DB] (ACID Transactions & Locking)
        ��─▖ [Redis In-Memory Store] (Distributed Mutexes & Cache)
        ⊜─▖ [Celery Background Workers] (Async Parsing & Notifications)
```

---

## ⚾��� Repository Documentation Suite

* **System Design Specification:** `docs/SYSTEM_DESIGN.md` & `docs/SYSTEM_DESIGN_CURRICULUM.md`
* **Debugging & Performance Report:** `docs/DEBUGGING_REPORT.md`
* **Production Incident Post-Mortem Runbook:** `docs/INCIDENT_POSTMORTEM_RUNBOOK.md`
* **Backend Interview Preparation:** `docs/INTERVIEW_PREP.md`
* **Professional Portfolio & Resume Guide:** `docs/PORTFOLIO_PROFILE.md`
* **Operations Handover Spec:** `docs/PROJECT_HANDOVER.md`
* **QA Sign-off Report:** `docs/QA_SIGNOFF_REPORT.md` & `docs/FINAL_TEST_LOGS.txt`
FINAL_TEST_LOGS.txt`
EINAL_TEST_LOGS.txt`