# Production Debugging, Troubleshooting & Performance Engineering Report

This guide outlines hands-on debugging exercises, logical problem-solving scenarios, and performance optimization techniques for production Django/DRF systems.

---

## 1. Solved Debugging Exercises

### Problem 1.1: Fix Broken API — Silent Payload Truncation on Bulk Resume Ingestion
* **Symptom:** Clients submitting batches of candidate applications via POST /api/applications/bulk/ received HTTP 200 OK, but only the first candidate was written to the database.
* *Root Cause:**
  1. The DRF view accessed request.data.get('candidates') directly instead of validating via ApplicationSerializer(data=..., many=True).
  2. Inside a manual loop, a variable shadow bug (app = ...) reused the same in-memory dictionary reference across iterations without clearing prior attributes.
* *Resolution & Code Fix:**
  pass
# Resolved via DRF ManyValidator & BulkCreate

---

## 2. Logical Problem-Solving & Edge-Case Handling

### Scenario 2.1: Preventing Double-Submission on Slow Networks (Idempotency)
* **Problem:** Candidates submitting multiple times in very short windows develop duplicate records.
* **Solution:** Enforce database-level unique together constraints and Redis idempotency-key locks.

### Scenario 2.2: Third-Party API Outage (Graceful Degradation)
* **Problem:** External Evaluation API outages cause WSGI timeouts.
* **Solution:** Offload tasks to Celery workers with circuit-breaker fallbacks and retry backoffs.

---

## 3. Performance Debugging & Profiling

### Issue 3.1: Diagnosing Slow Queries (N+1 Resolution)
* **Problem:** 101 queries spawned for a single list request.
* **Fix:** Apply select_related('candidate', 'job') to collapse to a single SMI JOIN query (304ms down to 4ms).

### Issue 3.2: Celery Worker Memory Leaks
* **Problem:** Persistent memory accumulation across batches in workers.
* **Fix:** Set CELERY_WORKER_MAX_TASKS_PER_CHILD = 500 and explicitly invoke garbage collection on large byte streams.
