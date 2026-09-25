# Distributed System Design Specification: ATS & AI Interview Platform

This document outlines the end-to-end system design, data flow pipelines, distributed queues, and trade-off analyses for our enterprise-grade Applicant Tracking System (ATS) and Autonomous AI Interview Engine.

---

## 1. ATS System Design

### 1.1 Resume Parsing Pipeline (Async Event-Driven)

Ingesting untrusted, polymorphic binaries (PDF, DOCX) requires an asynchronous, fault-tolerant extraction architecture that isolates compute-heavy operations from synchronous web workers.

```
+------------------+         +-----------------+         +-------------------+
|  Candidate Web   |  POST   |  Nginx / Django | Presign |  AWS S3 Private   |
|      Client      +-------->+   API Gateway   +-------->+    Bucket (Raw)   |
+--------+---------+         +--------+--------+         +---------+---------+
         |                            |                            |
         | Direct Multipart Stream    |                            |
         +-------------------------------------------------------->|
                                                                   |
                                                      S3 ObjectCreated Event
                                                                   |
                                                                   v
                                                         +---------+---------+
                                                         |   Celery / SQS    |
                                                         |  Ingestion Queue  |
                                                         +---------+---------+
                                                                   |
                                                                   v
+------------------+         +-----------------+         +---------+---------+
| Vector DB / RDS  | Updates |   Transformer   | Extract |   OCR / Textract  |
|  Parsed Entity   |<--------+ Entity Extractor|<--------+    Worker Pool    |
+------------------+         +-----------------+         +-------------------+
```

#### Pipeline Stages:
1. **Direct-to-S3 Upload:** Client initiates upload request. Django generates an S3 pre-signed upload URL. The client streams the binary directly to S3 under `/raw_resumes/<uuid>.ext`, preventing web server memory exhaustion.
2. **Event Notification & Queue Ingestion:** S3 triggers an `ObjectCreated` event, enqueueing a job into Celery via Redis/SQS.
3. **Malware & Sanitization Sandbox:** Isolated worker scans binary using ClamAV. Files containing macros, executable scripts, or malicious byte headers are rejected (`HTTP 422 / Status: INFECTED`).
4. **Text & Layout Extraction:**
   - **Structured PDFs:** Extracted via PDFMiner / PyPDF layout engines.
   - **Scanned Images/Unstructured PDFs:** Routed to OCR pipelines (Tesseract / AWS Textract) to extract raw text coordinates and tabular data.
5. **Entity Recognition & Normalization (NER):** Custom spaCy/transformer pipelines parse entities into structured JSON:
   - Contact Info, Education, Experience History, Skill sets, Certifications.
6. **Persistence & Vectorization:** Structured entities are committed to PostgreSQL, while normalized skill/experience embeddings are generated and stored in pgvector/Milvus.

---

### 1.2 Candidate Ranking System (Hybrid Vector & Heuristic Match)

To eliminate parsing hallucinations while maintaining semantic awareness, candidate matching operates on a dual-scoring model:

59807S_{\text{total}} = w_1 \cdot S_{\text{semantic}} + w_2 \cdot S_{\text{exact}} + w_3 \cdot S_{\text{experience}} - P_{\text{gap}}59807

```
Job Description ───► [ Transformer Embedding ] ──► Vector d_job
                                                          │
Candidate Resume ──► [ Transformer Embedding ] ──► Vector d_cand
                                                          │
                               Cosine Similarity: cos(θ) = (d_job · d_cand) / (||d_job|| ||d_cand||)
                                                          │
                                                          ▼
                                            [ Semantic Score: S_semantic ]
                                                          │
                                                          +──► [ Composite Match Index ] ──► Rank List
                                                          │
[ Hard Requirements Filter ] ───────────────► [ Exact Match Score: S_exact ]
(e.g., Python >= 3 yrs, Location, Visa)
```

1. **Semantic Scoring ({\text{semantic}}$):** Cosine similarity between dense vector representations of the Job Specification and Candidate Resume using `text-embedding-3-large` or fine-tuned BERT models.
2. **Exact Skill Overlap ({\text{exact}}$):** Jaccard similarity index across normalized skill ontologies (e.g., mapping `Django REST Framework`, `DRF`, and `Django APIs` to a unified canonical skill ID).
3. **Experience & Trajectory ({\text{experience}}$):** Normalized heuristic evaluating duration, seniority keywords (Lead, Staff, Senior), and tenure stability.
4. **Penalty Offsets ({\text{gap}}$):** Applied for missing non-negotiable regulatory qualifications (e.g., active certifications, license requirements).

---

### 1.3 Shortlisting Automation Engine

A deterministic Finite State Machine (FSM) executes transition logic based on configurable recruiter thresholds:

```
[ Application Ingested ] ──► [ Score Computation ]
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼ (Score >= Shortlist_Threshold)              ▼ (Score < Rejection_Threshold)
     [ Status: SHORTLISTED ]                       [ Status: REJECTED ]
               │                                             │
               ├─► Recruiter Dashboard Notification         └─► Grace-Period Rejection Email
               │                                                 (Configurable 48-hour delay)
               ▼
     [ Auto-Trigger AI Interview ]
```

* **Anti-Bias Filtering:** Personal Identifiable Information (PII) like name, gender, age, and zip code are scrubbed before feeding profiles to ranking models.
* **Safety Auditing:** Decisions are logged with transparent feature attribution weights to comply with automated employment decision tools (AEDT) regulations.

---

## 2. AI Interview System Design

### 2.1 Low-Latency AI Call Flow Architecture

Real-time audio conversational screening demands sub-800ms end-to-end voice-to-voice latencies to maintain natural dialogue flow.

```
+-----------+         +------------------+         +-------------------+
| Candidate | WebRTC  |  Media Gateway   | Stream  |   Speech-to-Text  |
|  Browser  +========>+ (LiveKit / Kurento+-------->+ (Deepgram / Whisper|
+-----+-----+ Audio   +--------+---------+ PCM     +---------+---------+
      ^                        ^                             | Real-time
      | Opus                   | Send Generated              v Tokens
      | Audio                  | Audio Stream      +---------+---------+
      |                        |                   |    LLM Dialogue   |
+-----+-----+         +--------+---------+ Tokens  |   Context Engine  |
| Candidate |<========+  Text-to-Speech  |<--------+  (GPT-4o / Claude)|
| Speaker   | Stream  | (Cartesia/Eleven)| Stream  +-------------------+
+-----------+         +------------------+
```

#### Latency Budget Allocation:
* **Audio Ingestion (WebRTC):** 30–50ms
* **Streaming STT (Voice Activity Detection + Word Finalization):** 150–200ms
* **LLM Time-To-First-Token (TTFT via Streaming):** 200–300ms
* **Streaming Text-to-Speech (First Audio Chunk):** 100–150ms
* **Transport Jitter Buffer:** 50ms
* **Total End-to-End Latency Target:** $\approx 530\text{ms} - 750\text{ms}$

---

### 2.2 Question Engine (Stateful Dynamic DAG)

Rather than following a rigid script, the interview progresses through a dynamically evaluated Directed Acyclic Graph (DAG):

```
                     [ Phase 1: Context & Introduction ]
                                      │
                                      ▼
                      [ Phase 2: Technical Deep Dive ]
                                      │
                        ┌─────────────┴─────────────┐
        (Answer Demonstrates Mastery)       (Answer Lacks Substance)
                        ▼                           ▼
        [ Increase Complexity Level ]       [ Probe Fundamental Concepts ]
                        │                           │
                        └─────────────┬─────────────┘
                                      ▼
                      [ Phase 3: System Architecture ]
                                      │
                                      ▼
                      [ Phase 4: Candidate Q&A / Close ]
```

* **Context Ingestion:** The engine initializes dialogue state with the candidate’s resume, parsed skill gaps, and target job competencies.
* **Follow-up Heuristics:** The system evaluates candidate responses for specificity:
  - If an answer contains vague buzzwords, the LLM generates targeted follow-up prompts (*"Can you elaborate on how you resolved thread contention in that Redis cluster?"*).
  - If an answer is complete, the state machine branches to the next competency node.

---

### 2.3 Automated Scoring & Rubric Matrix

The scoring engine evaluates the candidate post-interview across structured dimensions:

| Dimension | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **Technical Depth** | 5\%$ | Correctness of technical mechanics, edge-case awareness, algorithmic reasoning. |
| **Problem Solving** | 5\%$ | Structured approach, requirement clarification, trade-off analysis. |
| **Communication & Conciseness**| 0\%$ | Articulation clarity, structured explanations (STAR method), signal-to-noise ratio. |
| **Experience Verification** | 0\%$ | Consistency with claimed resume achievements, authentic project context. |

---

## 3. Scalability & Distributed Systems Trade-Offs

### 3.1 Synchronous vs. Queue-Based Processing

```
SYNCHRONOUS DESIGN (Anti-Pattern):
[ Client ] ──POST /application──► [ Django Server ] ────► [ S3 Upload ] (3s)
                                         │
                                         ├──────────────► [ Extract Text ] (4s)
                                         │
                                         ├──────────────► [ Call LLM API ] (5s)
                                         │
                                         ▼ (Total: 12+ seconds -> HTTP 504 Timeout)
                                  [ Return Response ]

QUEUE-BASED DESIGN (Production Standard):
[ Client ] ──POST /application──► [ Django Server ] ──► [ Redis / Celery ]
                                         │
                                         ▼ (15ms -> HTTP 202 Accepted)
                                  [ Return task_id ]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          [ Worker Node 1 ]                           [ Worker Node 2 ]
          - Resume OCR & Parsing                      - Audio Analysis & Scoring
          - Database Persistence                      - Cache Invalidation
```

---

### 3.2 Monolith vs. Microservices Architecture Strategy

| Dimension | Modular Monolith (Current) | Event-Driven Microservices (Scale) |
| :--- | :--- | :--- |
| **Operational Complexity** | Low (Single deployment unit, unified migrations). | High (Service discovery, distributed tracing, network latency). |
| **Data Consistency** | ACID Guarantees via PostgreSQL transactions. | Eventual Consistency via Sagas / Kafka event logs. |
| **Team Velocity** | Fast for small/mid-sized engineering teams. | Necessary when autonomous teams manage isolated bounded contexts. |
| **Failure Blast Radius** | High (Crash in monolithic code can impact all endpoints). | Low (Isolated service failures degrade gracefully). |
| **Recommendation** | **Retain Modular Monolith** until team size exceeds 25+ engineers or media streaming demands dedicated edge nodes. |
