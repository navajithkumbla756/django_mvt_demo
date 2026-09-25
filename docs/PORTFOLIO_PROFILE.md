# Professional Portfolio, Resume Optimization & Engineering Showcase

This document outlines ATS-optimized resume sections, quantified achievements, github presentation guidelines, and LinkedIn optimization assets.

---

## 1. Resume Optimization (ATS-Ready)

### Professional Summary
> Full-Stack Python & Django Developer with experience architecting high-concurrency RESTful APIs, PostgreSQL / Redis data layers, and Asynchronous worker pipelines (Celery/Redis). Proven track record optimizing database performance (reducing query latency from 340ms to 4ms via select_related), engineering distributed idempotency controls, and deploying production backends to AWS EC2 behind Nginx and Gunicorn.

### Key Project: Enterprise ATS Recruitment Portal & AI Screening Engine
* **Role:** Lead Backend & System Design Engineer
* **Tech Stack:** Python, Django, DRF, PostgreSQL, Redis, Celery, Nginx, Gunicorn, AWS EC2, OpenAPI/Swagger

#### Quantified Impact Bullet Points (STAR Method)
* **High-Concurrency API Design:** Engineered a recruitment platform processing multi-role candidate pipelines, implementing JWT authentication, custom Role-Based Access Control (RBAC), and OpenAPI 3.0 specifications.
* **Database & Query Optimization:** Diagnosed and eliminated N + 1 database bottlenecks across core job and application endpoints using Django's `select_related` and `prefetch_related`, dropping query roundtrips from 101 to 1 and slashing P99 latency by 85% (340ms down to 4ms).
* **Distributed Mutex & Concurrency:** Designed Redis-backed idempotency locks (`SET NZ EX`) to eliminate double-submission race conditions under high network latency, maintaining strict ACID guarantees.
* **Deadlock Prevention:** Enforced deterministic monotonic row-locking orders using PostgreSQL  select_for_update(), eliminating deadlocks during concurrent multi-recruiter status updates.
* **Background Task Offloading:** Built asynchronous resume parsing and notification workflows via Celery and Redis, incorporating task recycling thresholds (`CELERY_WORKER_MAX_TASKS_PER_CHILD = 500`) to prevent memory leaks in production workers.
* **Production DevOps & Reliability:** Deployed and maintained the system on AWS EC2 (Ubuntu 24.04) utilizing Gunicorn socket activation and Nginx reverse proxying, achieving 99.9% uptime.

---

## 2. GitHub
* **Live Swagger UI:** http://13.50.230.182/api/docs/
* **Public Schema (YAML):** http://13.50.230.182/api/schema/

## 3. LinkedIn Optimization
* **Headline:** Full-Stack Developer | Python, Django & DRF | PostgreSQL, Redis & AWS | High-Performance APIs
* **Core Skills:** Python, Django, Django REST Framework, PostgreSQLS, Redis, Celery, Nginx, Gunicorn, AWS EC2, ORM Optimization, System Design.
