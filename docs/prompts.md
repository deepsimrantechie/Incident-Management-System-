# Prompts and AI Usage Documentation

This file documents all prompts and plans used to build the IMS project with AI assistance (Claude).

## Initial Planning Prompt

"Help me build a Mission-Critical Incident Management System that:
- Ingests signals at 10,000/sec using Kafka
- Debounces 100 signals into 1 work item using Redis
- Stores raw signals in MongoDB and work items in PostgreSQL
- Uses Strategy Pattern for alerting and State Pattern for lifecycle
- Has a React dashboard with live feed, incident detail and RCA form
- Runs everything in Docker Compose"

## Architecture Decisions

### Why Kafka?
Kafka acts as a shock absorber between the ingestion API and the database.
If 10,000 signals hit the API at once and the database is slow, Kafka
holds them safely. The API never blocks or crashes.

### Why asyncio.Queue as buffer?
Even Kafka has latency. The in-memory buffer lets the API return 202
instantly for every signal. The background task drains the buffer into
Kafka at its own pace.

### Why PostgreSQL for work items?
Work items and RCA records need ACID compliance — if we create an RCA
and update the work item status, both must succeed or both must fail.
PostgreSQL transactions guarantee this.

### Why MongoDB for raw signals?
Raw signals arrive in high volume with flexible structure (different
metadata per component type). MongoDB handles this better than PostgreSQL.

### Why Redis for debouncing?
Redis key-value store with TTL (time to live) is perfect for debouncing.
Set a key with 10-second expiry — if key exists, work item already created.
Sub-millisecond lookup speed.

## Tech Stack Selection Prompt

"What tech stack should I use for:
- High throughput signal ingestion (10k/sec)
- Debouncing
- Async processing
- Strategy and State design patterns
- Simple React dashboard"

## Design Pattern Implementation

### Strategy Pattern prompt:
"Implement the Strategy Pattern in Python for alert prioritization.
RDBMS failure should be P0, Cache P2, API P1. Make it easy to add
new component types without changing existing code."

### State Pattern prompt:
"Implement the State Pattern for incident lifecycle management.
States: OPEN, INVESTIGATING, RESOLVED, CLOSED. Must enforce order.
Cannot skip states. CLOSED is terminal."

## Backpressure Handling Prompt

"How do I handle 10,000 signals/sec in FastAPI without crashing
if Kafka is slow? I need the API to return instantly."

Solution: asyncio.Queue as in-memory buffer + background drain task.

## Testing Prompt

"Write pytest unit tests for:
- State machine transitions
- Cannot close from OPEN or INVESTIGATING
- Alert priority per component type
- RCA validation (empty fields rejected)
- MTTR calculation"
