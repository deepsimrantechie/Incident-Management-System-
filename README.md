# Incident Management System (IMS)

> A  real-time Incident Management System built for the Zeotap Infrastructure/SRE Intern Assignment. Handles high-throughput signal ingestion, intelligent debouncing, workflow-driven incident lifecycle, and mandatory Root Cause Analysis.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![Kafka](https://img.shields.io/badge/Kafka-7.5-black) ![React](https://img.shields.io/badge/React-18-blue) ![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Design Patterns](#design-patterns)
- [How Backpressure is Handled](#how-backpressure-is-handled)
- [Debouncing Logic](#debouncing-logic)
- [Running Tests](#running-tests)
- [Mock Failure Simulation](#mock-failure-simulation)
- [Non-Functional Features](#non-functional-features)

---

## 📖 Overview

The IMS monitors a distributed stack (APIs, MCP Hosts, Distributed Caches, Async Queues, RDBMS, NoSQL stores) and manages failure mediation workflow. When components fail, signals are ingested at high throughput, intelligently grouped into Work Items, and tracked through a workflow until closure with a mandatory Root Cause Analysis.

### What it does
- Ingests up to **10,000 signals/second** without crashing
- **Debounces** 100 signals for the same component into 1 Work Item
- Routes **P0/P1/P2/P3 alerts** based on component type
- Tracks incidents through **OPEN → INVESTIGATING → RESOLVED → CLOSED**
- **Blocks closure** unless a complete RCA is submitted
- Automatically calculates **MTTR** (Mean Time To Repair)
- Shows everything on a **live auto-refreshing dashboard**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                       │
│           LiveFeed │ IncidentDetail │ RCAForm                    │
│                        port 5173                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP REST (axios)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                     │
│                          port 8000                                │
│                                                                   │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │ Rate Limiter│───▶│ Ingestion API│───▶│  Memory Buffer   │   │
│   │ 10k req/sec │    │ POST /signals│    │ asyncio.Queue    │   │
│   └─────────────┘    └──────────────┘    │ maxsize=50,000   │   │
│                                           └────────┬─────────┘   │
│                                                    │ drain        │
│                                           ┌────────▼─────────┐   │
│                                           │  Kafka Producer  │   │
│                                           └────────┬─────────┘   │
│                                                    │              │
│                                    ┌───────────────▼──────────┐  │
│                                    │  KAFKA: ims-signals topic │  │
│                                    └───────────────┬──────────┘  │
│                                                    │              │
│                                           ┌────────▼─────────┐   │
│                                           │  Kafka Consumer  │   │
│                                           └────────┬─────────┘   │
│                                                    │              │
│                          ┌─────────────────────────┼──────────┐  │
│                          │                          │          │  │
│                 ┌────────▼──────┐      ┌───────────▼──┐  ┌───▼─┐│
│                 │   MongoDB     │      │  PostgreSQL   │  │Redis││
│                 │ raw_signals   │      │  work_items   │  │cache││
│                 │ (audit log)   │      │  rca_records  │  │+ttl ││
│                 └───────────────┘      └───────────────┘  └─────┘│
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              Workflow Engine                              │   │
│   │  Strategy Pattern (alerting) + State Pattern (lifecycle) │   │
│   └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Frontend | React + Vite | 18 | Live dashboard UI |
| Styling | Tailwind CSS | 3 | Dark theme UI |
| HTTP Client | Axios | latest | API calls from frontend |
| Backend | Python FastAPI | 0.111 | Async REST API |
| ASGI Server | Uvicorn | 0.30 | Runs FastAPI |
| Message Queue | Apache Kafka | 7.5 | High-throughput ingestion |
| Kafka Library | aiokafka | 0.11 | Async Kafka client |
| Source of Truth | PostgreSQL | 16 | Work items, RCA records |
| Audit Log | MongoDB | 7 | Raw signal storage |
| Cache + Debounce | Redis | 7 | Hot path + TTL keys |
| DB Driver (PG) | asyncpg | 0.29 | Async PostgreSQL |
| DB Driver (Mongo) | Motor | 3.3 | Async MongoDB |
| DB Driver (Redis) | redis-py | 5.0 | Async Redis |
| Validation | Pydantic | 2.7 | Data validation |
| Testing | Pytest | 8.2 | Unit tests |
| Containerization | Docker Compose | v5 | All infra in one command |

---

## 📁 Project Structure

```
ims-project/
├── backend/
│   ├── config/
│   │   ├── settings.py        # Reads .env — all config in one place
│   │   ├── database.py        # PostgreSQL, MongoDB, Redis connections
│   │   └── init_db.py         # Creates DB tables on startup
│   ├── models/
│   │   └── signal.py          # Pydantic models + enums (Signal, RCARequest, Priority)
│   ├── workflow/
│   │   ├── alerting.py        # Strategy Pattern — P0/P1/P2/P3 per component
│   │   └── state_machine.py   # State Pattern — OPEN→INVESTIGATING→RESOLVED→CLOSED
│   ├── ingestion/
│   │   ├── producer.py        # Memory buffer + Kafka producer + throughput metrics
│   │   └── rate_limiter.py    # Sliding window rate limiter (10k/sec)
│   ├── consumer/
│   │   └── consumer.py        # Kafka consumer + debouncing + work item creation
│   ├── api/
│   │   ├── ingestion.py       # POST /signals and /signals/batch
│   │   ├── workitems.py       # Work item CRUD + RCA submission
│   │   └── health.py          # GET /health
│   ├── tests/
│   │   └── test_ims.py        # Unit tests (state machine, alerting, RCA validation)
│   ├── main.py                # FastAPI entry point — wires everything together
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (not in Git)
├── frontend/
│   └── src/
│       ├── api.js                    # All backend API calls (axios)
│       ├── App.jsx                   # Router + navbar
│       ├── main.jsx                  # React entry point
│       ├── index.css                 # Tailwind + global styles
│       └── components/
│           ├── LiveFeed.jsx          # Dashboard — auto-refreshes every 5s
│           ├── IncidentDetail.jsx    # Incident view + transition buttons
│           ├── RCAForm.jsx           # RCA submission form
│           ├── PriorityBadge.jsx     # Colored P0/P1/P2/P3 badge
│           └── StatusBadge.jsx       # Colored OPEN/CLOSED/etc badge
├── infra/
│   └── docker-compose.yml     # Kafka, Zookeeper, PostgreSQL, MongoDB, Redis
├── scripts/
│   └── mock_failure.py        # Simulates RDBMS outage + MCP failure + cache degradation
├── docs/
│   └── prompts.md             # All prompts and AI usage documentation
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites

- Docker Desktop (with WSL2 integration on Windows)
- Python 3.12+
- Node.js 20+
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ims-project.git
cd ims-project
```

### Step 2 — Start all infrastructure (databases + Kafka)

```bash
cd infra
docker compose up -d
```

Wait 30 seconds for all services to be ready. Verify with:

```bash
docker ps
```

You should see 5 containers running: `ims-kafka`, `ims-zookeeper`, `ims-postgres`, `ims-mongodb`, `ims-redis`

### Step 3 — Set up and start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows WSL: source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
[STARTUP] Initializing database tables...
PostgreSQL tables initialized
[STARTUP] Starting Kafka buffer flusher...
[STARTUP] Starting Kafka consumer...
[STARTUP] IMS Backend is ready!
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 4 — Set up and start the frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 5 — Open the dashboard

```
http://localhost:5173        ← Live Dashboard
http://localhost:8000/docs   ← Interactive API Docs
http://localhost:8000/health ← Health Check
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Response |
|---|---|---|---|
| GET | /health | Health check for all services | `{status, services, buffer_size}` |
| POST | /api/v1/signals | Ingest a single signal | `202 Accepted` |
| POST | /api/v1/signals/batch | Ingest up to 1000 signals | `202 Accepted` |
| GET | /api/v1/workitems | List all work items sorted by priority | Array of work items |
| GET | /api/v1/workitems/:id | Get work item + raw signals from MongoDB | `{work_item, signals}` |
| PATCH | /api/v1/workitems/:id/transition | Move to next status | `{status: INVESTIGATING}` |
| POST | /api/v1/workitems/:id/rca | Submit RCA and close incident | `{status: CLOSED, mttr_seconds}` |
| GET | /api/v1/workitems/:id/rca | Fetch RCA for a work item | RCA object |

### Example: Send a signal

```bash
curl -X POST http://localhost:8000/api/v1/signals \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "RDBMS_PRIMARY_01",
    "component_type": "RDBMS",
    "error_code": "DB_CONNECTION_FAILED",
    "message": "Connection pool exhausted"
  }'
```

Response:
```json
{
  "status": "accepted",
  "component_id": "RDBMS_PRIMARY_01"
}
```

---

## 🎨 Design Patterns

### Strategy Pattern — alerting.py

Each component type has its own alert strategy class. Swapping the class changes the behavior — no if/elif chains needed.

| Component Type | Strategy Class | Priority | Use Case |
|---|---|---|---|
| RDBMS | RDBMSAlertStrategy | P0 Critical | Database down |
| API | APIAlertStrategy | P1 High | API failures |
| QUEUE | QueueAlertStrategy | P1 High | Queue failures |
| NOSQL | NoSQLAlertStrategy | P1 High | NoSQL failures |
| CACHE | CacheAlertStrategy | P2 Medium | Cache degradation |
| MCP_HOST | MCPAlertStrategy | P2 Medium | MCP host issues |

### State Pattern — state_machine.py

Each lifecycle state is its own class that knows its valid transitions. You cannot skip states or go backwards.

```
OPEN ──▶ INVESTIGATING ──▶ RESOLVED ──▶ CLOSED
                                           ▲
                                     RCA required
```

| State | Can Close? | Next State |
|---|---|---|
| OPEN | No | INVESTIGATING |
| INVESTIGATING | No | RESOLVED |
| RESOLVED | Yes (after RCA) | CLOSED |
| CLOSED | Already closed | — |

---

## 🔧 How Backpressure is Handled

This is one of the most critical requirements — the system must handle 10,000 signals/sec without crashing even if the database is slow.

**The 4-layer defense:**

**Layer 1 — Rate Limiter**
Requests above 10,000/sec are rejected with HTTP 429 before they reach the buffer. Uses a sliding window algorithm with a deque data structure.

**Layer 2 — In-Memory Buffer**
Every accepted signal is placed into an `asyncio.Queue` (max 50,000 slots) instantly. The API returns 202 immediately without waiting for Kafka or the database.

**Layer 3 — Background Drain Task**
A background task runs every 10ms, draining up to 500 signals from the buffer into Kafka. This decouples ingestion speed from processing speed.

**Layer 4 — Drop Strategy**
If the buffer fills up (50,000 signals waiting), the oldest signal is dropped to make room for the newest. This prevents memory exhaustion while keeping the system alive.

**Result:** The system never crashes under load. It degrades gracefully by dropping the oldest signals only when absolutely necessary.

---

## ⚡ Debouncing Logic

**Problem:** 10,000 signals for the same failing component should not create 10,000 Work Items.

**Solution:** Redis-based debouncing with TTL

```
Signal arrives for RDBMS_PRIMARY_01
         │
         ▼
Check Redis key: "debounce:RDBMS_PRIMARY_01"
         │
    ┌────┴────┐
   Key        Key
  exists    not exist
    │            │
    ▼            ▼
Increment    Create new
signal_count  Work Item
in PostgreSQL in PostgreSQL
    │            │
    │        Set Redis key
    │        with 10s TTL
    │            │
    └────┬───────┘
         ▼
  Link raw signal to
  Work Item in MongoDB
```

After 10 seconds the Redis key expires automatically. New signals for the same component will create a fresh Work Item.

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_ims.py -v
```

### Test Coverage

| Test Class | What is tested |
|---|---|
| TestStateMachine | OPEN→INVESTIGATING→RESOLVED→CLOSED transitions |
| TestStateMachine | Cannot close from OPEN or INVESTIGATING |
| TestStateMachine | CLOSED raises error on further transition |
| TestAlertStrategy | RDBMS gets P0, Cache gets P2, API gets P1 |
| TestAlertStrategy | Alert message contains component ID |
| TestAlertStrategy | P0 message contains CRITICAL keyword |
| TestRCAValidation | Valid RCA passes validation |
| TestRCAValidation | MTTR calculated correctly in seconds |
| TestRCAValidation | Empty fix_applied is rejected |
| TestRCAValidation | Empty prevention_steps is rejected |
| TestSignalModel | Valid signal created successfully |
| TestSignalModel | Timestamp auto-set if not provided |
| TestSignalModel | Invalid component type raises error |

---

## 🔥 Mock Failure Simulation

Run this script to simulate a real failure scenario across 4 components:

```bash
cd backend
source venv/bin/activate
python3 ../scripts/mock_failure.py
```

### What it simulates

| Scenario | Component | Signals | Expected Work Items |
|---|---|---|---|
| RDBMS outage | RDBMS_PRIMARY_01 | 150 | 1 (debounced) |
| MCP Host failure | MCP_HOST_01 | 50 | 1 (debounced) |
| Cache degradation | CACHE_CLUSTER_01 | 30 | 1 (debounced) |
| API error spike | API_GATEWAY_01 | 20 | 1 (debounced) |

Total: 250 signals → 4 Work Items (debouncing working correctly)

---

## ✨ Non-Functional Features

| Feature | Implementation | Details |
|---|---|---|
| Rate Limiting | Sliding window deque | 10,000 req/sec, HTTP 429 on breach |
| Throughput Metrics | Console logging | Signals/sec printed every 5 seconds |
| Health Endpoint | /health | Checks PostgreSQL, MongoDB, Redis + buffer size |
| Transactional RCA | PostgreSQL transaction | RCA insert + work item close are atomic |
| CORS | FastAPI middleware | Configured for frontend-backend communication |
| Async throughout | asyncio + await | Every DB and Kafka call is non-blocking |
| Retry Logic | KafkaConnectionError catch | Retries Kafka connection every 2 seconds |
| Gzip Compression | Kafka producer | Reduces bandwidth for high-volume signals |
| Batch Processing | Kafka linger_ms=5 | Groups signals into batches for efficiency |

---

## 👩‍💻 Author

**Simrandeep**
