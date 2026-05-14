# CartIQ — Real-Time E-Commerce Analytics Pipeline

> A production-grade event-driven analytics platform processing e-commerce events in real time via Apache Kafka, with stream aggregation, dual-write persistence, and a live React dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CartIQ System                               │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐ │
│  │  Simulator   │────▶│ Ingestion API│────▶│   Apache Kafka      │ │
│  │  (50 threads)│     │  FastAPI     │     │  cartiq_events      │ │
│  │  ~38 eps     │     │  port 8001   │     │  topic              │ │
│  └──────────────┘     └──────────────┘     └──────────┬──────────┘ │
│                                                        │            │
│                                            ┌───────────▼──────────┐ │
│                                            │  Stream Processor    │ │
│                                            │  kafka-python        │ │
│                                            │  20-thread pool      │ │
│                                            └──────┬────────┬──────┘ │
│                                                   │        │        │
│                                        ┌──────────▼─┐  ┌───▼──────┐│
│                                        │   Redis    │  │PostgreSQL││
│                                        │ aggregates │  │raw events││
│                                        │ sub-ms read│  │ forever  ││
│                                        └──────┬─────┘  └──────────┘│
│                                               │                     │
│                                    ┌──────────▼──────────┐          │
│                                    │  Analytics API      │          │
│                                    │  FastAPI port 8002  │          │
│                                    │  SSE log streaming  │          │
│                                    └──────────┬──────────┘          │
│                                               │                     │
│                                    ┌──────────▼──────────┐          │
│                                    │  React Dashboard    │          │
│                                    │  port 5173          │          │
│                                    │  polls every 5s     │          │
│                                    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11 | Typed, modern, async support |
| Ingestion API | FastAPI + Uvicorn | Async, auto docs, 202 Accepted pattern |
| Message Queue | Apache Kafka | Decoupled, durable, industry standard |
| Stream Processor | kafka-python + ThreadPoolExecutor | 20-thread parallel processing |
| Real-time Cache | Redis (ZSET, sorted sets, lists) | Sub-millisecond aggregates |
| Persistence | PostgreSQL + SQLAlchemy | Raw event audit trail, forever |
| Analytics API | FastAPI + SSE | REST + Server-Sent Events for log streaming |
| Dashboard | React 18 + TypeScript + Tailwind + Framer Motion | Glassmorphism UI, live charts |
| Charts | Recharts | Area, bar, donut charts |
| Containerization | Docker + docker-compose | One command to run everything |
| DB Design | Dual-write pattern | Redis for speed, PostgreSQL for durability |

---

## Events Tracked

| Event | Description |
|---|---|
| `product_viewed` | User viewed a product page |
| `cart_added` | Item added to cart |
| `cart_removed` | Item removed from cart |
| `purchase_completed` | Order placed successfully |
| `payment_failed` | Payment declined |

---

## Real-Time Analytics

| Metric | Implementation |
|---|---|
| Total Revenue | Redis `INCRBYFLOAT` — atomic float increment |
| Top Selling Products | Redis Sorted Set `ZINCRBY` — auto-ranked |
| Active Users (5min window) | Redis ZSET with timestamps — sliding window |
| Event Counts | Redis `INCR` per event type |
| Recent Events Feed | Redis List `LPUSH` + `LTRIM` — last 15 |
| Revenue History | Redis List — last 20 data points for chart |

---

## Key Engineering Decisions

### Why Kafka?
Decouples ingestion from processing. If the processor is slow or down, events queue in Kafka — nothing is lost. Ingestion API returns `202 Accepted` immediately without waiting for processing, enabling high throughput.

### Why Dual-Write (Redis + PostgreSQL)?
- **Redis** — fast, real-time. Dashboard reads aggregates in sub-millisecond. But Redis data is volatile — restart clears it.
- **PostgreSQL** — persistent, queryable. Every raw event saved forever. Enables historical queries, audit trails, and replaying events.
- This is the industry standard pattern at Visa, Amex, and Stripe.

### Why Sliding Window for Active Users?
A simple Redis Set with TTL would reset the entire window at once. Instead, each user is stored in a Sorted Set with their timestamp as score. On every read, scores older than 5 minutes are removed (`ZREMRANGEBYSCORE`). This gives an accurate rolling 5-minute count without ever resetting.

### Why 202 Accepted?
Ingestion API returns `202 Accepted` not `200 OK`. This is intentional — the event is received and queued, but not yet processed. Returning 200 would be semantically incorrect. This is how production payment systems work.

### Why 20 Threads in Processor?
Event processing is I/O bound — mostly Redis writes and PostgreSQL inserts. CPU is rarely the bottleneck. 20 threads allows significant parallel throughput on a single consumer without needing multiple Kafka consumer instances.

---

## Performance

| Metric | Value |
|---|---|
| Sustained throughput | ~38 events/sec (local machine) |
| Peak throughput | ~90 events/sec |
| Queue depth at 38 eps | 0 (fully drained) |
| PostgreSQL events stored | 10,000+ per run |
| Redis read latency | < 1ms |
| Dashboard poll interval | 5 seconds |
| Active users window | 5 minutes (sliding) |

---

## Services

| Service | Port | Description |
|---|---|---|
| Ingestion API | 8001 | Receives events, publishes to Kafka |
| Analytics API | 8002 | Reads Redis, serves dashboard data + SSE logs |
| React Dashboard | 5173 | Live charts, KPIs, event feed, infra monitor |
| Kafka | 9092 | Internal · 29092 External (local dev) |
| PostgreSQL | 5432 | Raw event storage |
| Redis | 6379 | Real-time aggregates |

---

## API Reference

### Ingestion API

#### `POST /api/v1/events`
Accepts single event or batch.

```json
{
  "event_type": "purchase_completed",
  "user_id": "user_123",
  "product_id": "prod_456",
  "product_name": "Nike Air Max",
  "price": 4999.99,
  "quantity": 1
}
```

Response:
```json
{ "status": "accepted", "processed": 1, "failed": 0 }
```

---

### Analytics API

#### `GET /api/v1/analytics/dashboard`
Single aggregated endpoint for the dashboard.

```json
{
  "revenue": { "total_revenue": 560182.6, "currency": "INR" },
  "top_products": {
    "products": [{ "product_name": "iPhone 15 Pro", "purchase_count": 142 }]
  },
  "event_counts": {
    "product_viewed": 6331, "cart_added": 1120,
    "purchase_completed": 572, "payment_failed": 234, "total": 8257
  },
  "active_users": { "active_users": 535, "window": "last 5 minutes" },
  "recent_events": [...],
  "revenue_history": [...]
}
```

#### `GET /api/v1/analytics/infra`
Redis + Kafka infrastructure stats.

#### `GET /api/v1/analytics/logs/{service}`
SSE stream of live container logs. `service` = `redis` or `kafka`.

#### `POST /api/v1/analytics/simulator/start`
Start the event simulator via Docker API.

#### `POST /api/v1/analytics/simulator/stop`
Stop the event simulator.

#### `GET /api/v1/analytics/simulator/status`
```json
{ "status": "running", "is_running": true, "eps": 38.2 }
```

---

## Running Locally

### Prerequisites
- Docker + docker-compose
- Node.js 20+

### Start everything

```bash
git clone https://github.com/chetanandmeher/cartiq
cd cartiq
docker-compose up --build
```

### Start Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### URLs

| Service | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| Infra Monitor | http://localhost:5173/infra |
| Ingestion API Docs | http://localhost:8001/docs |
| Analytics API Docs | http://localhost:8002/docs |

### Start Simulator via Dashboard
Click the **▶ play button** in the top bar. Events start flowing immediately.

---

## Database Schema

```sql
CREATE TABLE events (
    event_id    VARCHAR PRIMARY KEY,
    event_type  VARCHAR NOT NULL,
    user_id     VARCHAR NOT NULL,
    product_id  VARCHAR NOT NULL,
    product_name VARCHAR NOT NULL,
    price       FLOAT NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    timestamp   TIMESTAMP,
    extra_data  JSON
);
```

Indexed on `event_type`, `user_id`, `timestamp` for fast analytical queries.

---

## Project Structure

```
cartiq/
├── services/
│   ├── ingestion/          # FastAPI event intake
│   │   └── app/
│   │       ├── main.py
│   │       ├── routes.py
│   │       ├── schemas.py
│   │       ├── kafka_producer.py
│   │       └── config.py
│   ├── processor/          # Kafka consumer + Redis aggregator
│   │   └── app/
│   │       ├── main.py     # 20-thread consumer
│   │       ├── agents.py
│   │       ├── aggregators.py
│   │       ├── models.py   # SQLAlchemy Event model
│   │       ├── database.py
│   │       └── enums.py    # Single source of truth
│   ├── analytics/          # FastAPI query API + SSE
│   │   └── app/
│   │       ├── main.py
│   │       ├── routes.py
│   │       ├── schemas.py
│   │       └── enums.py
│   └── simulator/          # Load simulator Docker service
├── dashboard/              # React + TypeScript frontend
│   └── src/
│       └── components/
│           ├── KPICards.tsx
│           ├── ChartsArea.tsx
│           ├── LiveFeed.tsx
│           ├── SimulatorControl.tsx
│           └── InfraPage.tsx
├── scripts/
│   └── simulate_events.py  # Local dev simulator
├── docker-compose.yml
└── README.md
```

---

## Resume Line

> *"Built CartIQ, a real-time e-commerce analytics pipeline processing events via Apache Kafka with 20-thread parallel stream processing, dual-write pattern (Redis + PostgreSQL), sliding window active user tracking, SSE log streaming, and a live React dashboard with simulator control via Docker API."*

---

## What This Demonstrates

- **Event-driven architecture** — Kafka decoupling, 202 Accepted pattern
- **Real-time stream processing** — parallel consumer with thread pool
- **Dual-write pattern** — Redis for speed, PostgreSQL for durability
- **Systems thinking** — sliding window, atomic operations, connection pooling
- **Full stack** — Python microservices + React frontend
- **DevOps** — Docker, multi-service orchestration, container management via API
- **Production patterns** — idempotency, retry logic, graceful degradation
