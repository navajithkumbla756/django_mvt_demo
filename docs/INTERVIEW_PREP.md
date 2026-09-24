# Backend Engineering & Technical Interview Preparation Manual

This preparation manual covers core Django, Django REST Framework (DRF), distributed systems, caching, asynchronous processing, load balancing, and system design concepts, using production architectural patterns from our ATS platform.

---

## 1. Django & DRF Deep Dive

### 1.1 ORM Internals & Query Optimization
* **QuerySets are Lazy:** Django QuerySets do not execute SQL queries upon declaration. Database evaluation occurs only when the QuerySet is evaluated: during iteration, list conversion (`list(qs)`), slicing with a step, boolean checks (`bool(qs)` or `exists()`), or serialization.
* **The N+1 Query Problem:**
  * **The Issue:** Querying $N$ records and sequentially accessing a foreign key or many-to-many relationship causes 1 query for the initial model plus $N$ sequential queries for the related models.
  * **`select_related` (SQL JOIN):** Optimizes single-valued relationships (ForeignKey, OneToOne) by performing an SQL `INNER JOIN` or `LEFT OUTER JOIN` in a single database round-trip.
    ```python
    # 1 database query
    applications = Application.objects.select_related('candidate', 'job').filter(job__employer=user)
    ```
  * **`prefetch_related` (In-Memory Join):** Optimizes multi-valued relationships (ManyToManyField, reverse ForeignKey) by executing separate queries and linking the resulting records in Python memory.
    ```python
    # 2 database queries total
    jobs = Job.objects.prefetch_related('applications').all()
    ```
* **Selective Field Evaluation:**
  * `only('field1', 'field2')`: Fetches only specified columns alongside the primary key.
  * `defer('large_field')`: Defers fetching heavy text/binary fields until explicitly accessed.
* **Bulk Operations:**
  * `bulk_create()` and `bulk_update()` batch multiple records into minimal SQL statements, reducing overhead.
  * *Important trade-off:* Bulk operations do **not** invoke `model.save()`, do **not** trigger `pre_save`/`post_save` signals, and do not modify auto-timestamps unless configured explicitly.

### 1.2 Signals vs. Middleware

| Dimension | Django Middleware | Django Signals (`post_save`, etc.) |
| :--- | :--- | :--- |
| **Scope** | Global request/response lifecycle. | Model and framework event triggers. |
| **Common Use Cases** | Request tracing, rate limiting, header manipulation (CORS/security), authentication parsing. | Decoupled cross-app event reactions (e.g., initializing a profile after a user is saved). |
| **Execution** | Wraps the entire WSGI/ASGI handler flow synchronously. | Dispatched synchronously within the active thread and database transaction. |
| **Gotchas** | Heavy database queries in middleware delay every single endpoint on the server. | Bypassed by `bulk_create` and `QuerySet.update()`; can make control flow harder to trace. |

* **Interview Takeaway:** Prefer explicit Service Layer methods over signals for critical business workflows. Keep middleware lightweight and strictly focused on HTTP boundaries.

### 1.3 DRF Architecture & Request Pipeline
1. **`initialize_request()`:** Wraps the standard WSGI `HttpRequest` into a DRF `Request`, providing uniform access to `.data` and configured authentication handlers.
2. **`initial()`:**
   * **Authentication (`perform_authentication()`):** Lazily evaluates credentials (e.g., checking the JWT Bearer token).
   * **Permissions (`check_permissions()`):** Runs checks such as `IsAuthenticated` or `IsRecruiter`.
   * **Throttling (`check_throttles()`):** Enforces request rate limits using Redis or memory storage.
3. **Dispatch & Method Handler:** Dispatches to `get()`, `post()`, etc.
4. **Serialization & Validation:** Runs `to_internal_value()` -> `validate_<field>()` -> `validate()`.
5. **`handle_exception()`:** Normalizes Python/Django exceptions into standard JSON error responses.

---

## 2. Backend Architecture Concepts

### 2.1 REST API Design & HTTP Semantics
* **HTTP Verbs:**
  * `GET`: Safe and idempotent data retrieval.
  * `POST`: Non-idempotent resource creation.
  * `PUT`: Idempotent full replacement of a resource.
  * `PATCH`: Partial resource update.
  * `DELETE`: Idempotent resource removal.
* **Status Codes:**
  * `200 OK`: Successful read or update.
  * `201 Created`: Resource successfully created.
  * `204 No Content`: Successful request with an empty response body (typical for deletes).
  * `400 Bad Request`: Client-side validation failure.
  * `401 Unauthorized`: Authentication missing or token invalid.
  * `403 Forbidden`: Authenticated user lacks permission to access the resource.
  * `404 Not Found`: Target entity does not exist.
  * `409 Conflict`: Request conflicts with current resource state (e.g., duplicate unique constraint).
  * `429 Too Many Requests`: Rate limit threshold exceeded.
* **Idempotency Keys:**
  * Critical POST endpoints (like billing transactions) accept an `Idempotency-Key` header with a unique UUID. The application stores the response in Redis for a set TTL to prevent duplicate operations on network retries.

### 2.2 Caching Strategies
* **Cache-Aside (Lazy Loading):** The application queries the cache (e.g., Redis) first. On a cache miss, it reads from the database, writes the result to the cache with a Time-To-Live (TTL), and returns the payload.
* **Write-Through:** Updates are written to the database and cache simultaneously, ensuring strong consistency at the cost of higher write latency.
* **Preventing Cache Stampedes:** High-traffic cache key expirations can cause thousands of requests to hit the database at once. Mitigations include:
  * Distributed locks around cache repopulation.
  * Probabilistic early cache regeneration (XFetch).

### 2.3 Asynchronous Processing & Background Queues
* **Why Decouple:** Long-running workloads (e.g., resume parsing, audio transcription, external AI inference, sending emails) should not block the web server's request-response cycle.
* **Queue Lifecycle:** The API controller publishes an event/job payload to a message broker (Redis, RabbitMQ) and returns an HTTP `202 Accepted` with a task ID. Asynchronous workers (Celery) consume and process tasks independently.

---

## 3. Scaling & Distributed Systems

### 3.1 Scaling Dimensions
* **Vertical Scaling (Scale Up):** Adding CPU, RAM, or IOPS to a single machine. Limited by hardware maximums and creates a single point of failure.
* **Horizontal Scaling (Scale Out):** Adding more application servers behind a load balancer. Requires stateless application nodes, storing session state in Redis and binary files in cloud object storage (e.g., AWS S3).

### 3.2 Load Balancing Mechanics
* **Layer 4 (Transport Layer):** Routes TCP/UDP traffic based on IP address and port without inspecting HTTP headers. Ultra-high throughput.
* **Layer 7 (Application Layer):** Inspects HTTP/HTTPS headers, paths, and cookies. Enables path-based routing (e.g., `/api/resumes/` to specific workers) and SSL termination.
* **Balancing Algorithms:** Round Robin, Least Connections, IP Hash (for session affinity), Weighted Response Time.

### 3.3 Database Scaling
* **Connection Pooling:** Tools like PgBouncer maintain a pool of reusable database connections, preventing connection exhaustion under high concurrency.
* **Read/Write Splitting:** The primary database node handles all writes (`INSERT`, `UPDATE`, `DELETE`), while read replicas serve read-only traffic (`SELECT`).
* **Database Sharding:** Horizontally partitioning large tables across distinct physical database instances using a shard key (e.g., `tenant_id` or `company_id`).

---

## 4. Key Interview Q&A

### Q1: Explain the end-to-end JWT authentication flow and how token revocation is handled.
**Answer:**
1. The client sends user credentials (`email`, `password`) to `/api/auth/token/`. The server verifies the password hash using PBKDF2.
2. Upon successful authentication, the server signs two tokens: an **Access Token** (short-lived, e.g., 15 minutes) and a **Refresh Token** (long-lived, e.g., 7 days).
3. The client includes the access token in the `Authorization: Bearer <token>` header for subsequent requests. The server validates the cryptographic signature statelessly without querying the database, keeping API latency minimal.
4. When the access token expires, the client calls `/api/auth/token/refresh/` with the refresh token to get a new access token.
5. For **revocation/logout**, because JWTs are stateless, our platform uses a token blacklist. The refresh token's unique identifier (`jti`) is stored in a Redis or database blocklist table, preventing the token from generating new access tokens.

### Q2: How does the ATS handle secure document uploads and prevent unauthorized resume access?
**Answer:**
1. **Private S3 Storage:** Resumes are uploaded to an AWS S3 bucket with all public access blocked (`BlockPublicAcls = True`).
2. **Immutable Snapshots:** Resumes submitted during application are stored under immutable, non-deterministic keys (`/resumes/snapshots/<uuid>.pdf`). Updates to candidate profiles do not alter previously submitted applications.
3. **AWS SigV4 Pre-signed URLs:** Recruiter access is verified through a backend service layer (`DocumentAccessService`). If the recruiter owns the job posting, the backend generates a short-lived **AWS Signature Version 4 (SigV4)** pre-signed URL (e.g., 300 seconds TTL). The recruiter downloads the file directly from S3, eliminating server bandwidth bottlenecks while keeping the bucket private.

### Q3: How do you design a REST API to handle sudden 100x traffic spikes?
**Answer:**
1. **Stateless Web Nodes:** Ensure application containers carry no local state, allowing auto-scaling groups to add instances based on CPU or request latency metrics.
2. **Caching:** Place Redis in front of read-heavy endpoints using the Cache-Aside pattern, serving common reads from memory.
3. **Connection Pooling:** Use PgBouncer in front of PostgreSQL to prevent connection spikes from overwhelming database process limits.
4. **Asynchronous Processing:** Move slow, external, or resource-intensive tasks (AI parsing, notifications) to background queues (Celery/Redis) with HTTP 202 responses.
5. **Rate Limiting:** Enforce throttling at the Nginx and DRF layers to shed abusive traffic and maintain service availability.
