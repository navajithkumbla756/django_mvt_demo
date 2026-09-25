# Production Incident Post-Mortem, Recovery & Operations Runbook

This guide trains developers in diagnosing live production failures, analyzing system and application logs, executing graceful recoveries, and writing comprehensive post-mortem reports.

---

## 1. Production Log Analysis Methodology

### 1.1 Application & Error Logs (Gunicorn / Django)
Diagnosing backend failures requires rapid inspection of systemd and WSGI worker streams:
* Inspect the last 200 worker logs:
  `sudo journalctl -u gunicorn -n 200 --no-pager`
* Stream live logs in real time during an active incident:
  `sudo journalctl -u gunicorn -f`
* Inspect Django application-specific error traces:
  `tail -n 100 /var/www/django_app/logs/django_error.log`

### 1.2 Web Server Logs (Nginx Reverse Proxy)
Differentiate client timeouts from application crashes:
* Access logs (traffic spikes, request status codes, client IPs):
  `sudo tail -n 100 /var/log/nginx/access.log`
* Error logs (upstream connection refused, 502/504 errors):
  `sudo tail -n 100 /var/log/nginx/error.log`
* Key metric correlation: Compare `$request_time` (total time taken) with `$upstream_response_time` (backend processing time) to isolate network latency from application delays.

---

## 2. Real Production Failure Scenarios

### 2.1 Scenario A: Total API Worker Crash (502 Bad Gateway)
* **Symptom:** Nginx returns `HTTP 502 Bad Gateway` across all endpoints; Gunicorn socket is active but workers terminate immediately.
* **Root Cause:** A newly deployed dependency or memory-heavy task triggered an unhandled exception during application boot, or Linux OOM (Out Of Memory) killer killed all Gunicorn worker processes.
* **Diagnosis:**
  `sudo journalctl -u gunicorn -n 50 --no-pager`
  `dmesg -T | grep -i oom`
* **Recovery:**
  1. Restart socket and service: `sudo systemctl restart gunicorn.socket gunicorn.service`
  2. If memory exhaustion persists, reduce worker count temporarily or scale instance memory.

### 2.2 Scenario B: Payment & Webhook Failures
* **Symptom:** Customers successfully complete checkout on Stripe/Razorpay, but accounts/orders stay in `PENDING` state.
* **Root Cause:**
  1. Webhook signature mismatch due to rotated secrets.
  2. Celery worker responsible for processing webhooks crashed or experienced broker connection failure.
* **Diagnosis:**
  * Search logs for signature verification errors:
    `sudo journalctl -u gunicorn | grep -i "webhook_signature_verification_failed"`
* **Recovery:**
  1. Verify active signing secret in environment variables.
  2. Replay unacknowledged webhooks from the payment provider dashboard or CLI.
  3. Ensure webhook consumer is strictly idempotent.

### 2.3 Scenario C: External AI Call Provider Outage / Latency Spike
* **Symptom:** Resume parsing or AI interview endpoints hang for 30+ seconds, eventually returning `HTTP 504 Gateway Timeout`.
* **Root Cause:** Upstream AI provider (OpenAI / Deepgram / Anthropic) is experiencing rate-limiting (HTTP 429) or elevated latency, blocking synchronous web workers.
* **Recovery:**
  1. Trigger circuit breaker to fail fast and avoid consuming server threads.
  2. Degrade gracefully: switch to heuristic fallback scoring.
  3. Enqueue requests into Celery with exponential backoff and jitter.

---

## 3. Production Recovery Strategies

### 3.1 Service Restarts & Graceful Reloads
* Graceful zero-downtime Gunicorn reload (completes active requests):
  `sudo systemctl reload gunicorn.service`
* Hard restart if workers are frozen or deadlocked:
  `sudo systemctl restart gunicorn.socket gunicorn.service`
* Reload Nginx reverse proxy configurations:
  `sudo nginx -t && sudo systemctl reload nginx`

### 3.2 Deployment Rollbacks
When a faulty commit causes production regressions:
1. Locate last stable commit hash:
   `git log --oneline -5`
2. Roll back working tree cleanly:
   `git checkout <STABLE_COMMIT_HASH>`
3. Revert database migrations if necessary:
   `python3 manage.py migrate <app_name> <previous_migration_name>`
4. Restart application workers:
   `sudo systemctl restart gunicorn.service`

### 3.3 Data Recovery & WAL Point-in-Time Recovery (PITR)
* Ensure automated daily pg_dump backups are stored off-instance (e.g., S3).
* For point-in-time recovery, replay PostgreSQL Write-Ahead Logs (WAL) up to the exact transaction prior to data corruption.


---

## 3. Production Recovery Strategies

### 3.1 Service Restarts & Graceful Reloads
* **Graceful WSGI Worker Reload (Zero Downtime):**
  `sudo systemctl reload gunicorn.service`
* **Hard Restart (Hung / Unresponsive Sockets):**
  `sudo systemctl restart gunicorn.socket gunicorn.service`
* **Nginx Configuration Reload:**
  `sudo nginx -t && sudo systemctl reload nginx`

### 3.2 Deployment Rollbacks
When a faulty commit causes production regressions:
1. Locate the last stable commit hash:
   `git log --oneline -5`
2. Roll back working tree cleanly:
   `git checkout <STABLE_COMMIT_HASH>`
3. Revert database migrations if necessary:
   `python3 manage.py migrate <app_name> <previous_migration_name>`
4. Restart application workers:
   `sudo systemctl restart gunicorn.service`

### 3.3 Data Recovery & WAL Point-in-Time Recovery (PITR)
* Ensure automated daily `pg_dump` backups are stored off-instance in S3.
* For transactional recovery without data loss, replay PostgreSQL Write-Ahead Logs (WAL) up to the exact timestamp prior to corruption.

---

## 4. Production Incident Post-Mortem & RCA Template

Every severity 1 or 2 production incident requires a completed Post-Mortem document within 24 hours of resolution.

### Post-Mortem Specification

| Field | Description |
| :--- | :--- |
| **Incident Title** | Short descriptive title (e.g., "Gunicorn Worker OOM during Bulk Ingestion") |
| **Severity** | Sev-1 (Critical Outage) / Sev-2 (Degraded Performance) |
| **Outage Window** | Start timestamp, end timestamp, and total duration (UTC) |
| **Lead Responder** | Primary on-call or responding engineer |

### 1. Executive Summary
Brief non-technical overview of the outage, user impact, and final resolution.

### 2. Impact Metrics
* **Total Affected Requests / Users:** Number of impacted sessions.
* **Error Rate Peak:** Maximum percentage of 5xx errors recorded.
* **SLA & Business Impact:** Financial or contractual impact.

### 3. Incident Timeline (UTC)
* **HH:MM** - Automated monitoring alert triggered (e.g., HTTP 502 spike).
* **HH:MM** - Incident responder joined war room and confirmed worker crash via `journalctl`.
* **HH:MM** - Root cause isolated (e.g., Linux OOM killer invoked due to unbuffered 120MB PDF payload).
* **HH:MM** - Service restored via socket restart.
* **HH:MM** - Permanent hotfix deployed and verified.

### 4. Root Cause Analysis (5-Whys Method)
1. **Why did the API return 502 Bad Gateway?** All Gunicorn worker processes were terminated by the OS.
2. **Why did the OS terminate workers?** Memory consumption exceeded physical RAM limits, triggering the Linux OOM killer.
3. **Why did memory spike?** A user uploaded an uncompressed 120MB PDF for inline resume parsing.
4. **Why did the server accept a 120MB file?** Web server request body limits (`client_max_body_size`) were unset in Nginx.
5. **Why was it parsed in-process?** Ingestion ran synchronously inside the web worker instead of being offloaded to Celery.

### 5. Corrective & Preventive Measures
* [x] Enforce Nginx `client_max_body_size 15M;` to reject oversize payloads at the proxy layer.
* [x] Enforce Celery worker memory ceilings (`CELERY_WORKER_MAX_MEMORY_PER_CHILD = 300000`).
* [x] Add CloudWatch alarms for EC2 RAM utilization > 80%.
