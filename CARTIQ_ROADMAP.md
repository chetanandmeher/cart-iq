# CartIQ — Project Roadmap & Progress Tracker

> Real-Time E-Commerce Event Analytics Pipeline
> Stack: Python 3.11 · FastAPI · Apache Kafka · PostgreSQL · Redis · React · Docker

---

## Project Goal
Build a production-grade event-driven analytics pipeline that ingests e-commerce events in real time, processes them through Kafka, aggregates them, and displays live insights on a dashboard.

---

## Architecture

```
Event Producer (any app / simulator)
        ↓
Ingestion API (FastAPI) — receives events via REST
        ↓
Apache Kafka (events topic) — decouples producer from processor
        ↓
Stream Processor (Faust) — consumes, aggregates, enriches events
        ↓
PostgreSQL (raw events)      Redis (real-time aggregates)
        ↓
Analytics API (FastAPI) — query processed data
        ↓
Live Dashboard (React + TypeScript) — charts, KPIs, live feed
```

---

## Events We Track
| Event | Description |
|---|---|
| `product_viewed` | User viewed a product page |
| `cart_added` | Item added to cart |
| `cart_removed` | Item removed from cart |
| `purchase_completed` | Order placed successfully |
| `payment_failed` | Payment was declined |

---

## Analytics We Compute
| Metric | How |
|---|---|
| Revenue per minute / hour | Sum of `purchase_completed` amounts |
| Top selling products | Count `purchase_completed` by product |
| Cart abandonment rate | `cart_added` vs `purchase_completed` ratio |
| Failed payment rate | `payment_failed` / total checkout attempts |
| Active users right now | Unique users in last 5 minutes |

---

## Tech Stack
| Layer | Tech | Why |
|---|---|---|
| Language | Python 3.11 | Typed, modern, fast to build |
| Web Framework | FastAPI | Async, auto docs, production standard |
| Message Queue | Apache Kafka | Industry standard for event streaming |
| Stream Processor | Faust | Python-native Kafka stream processing |
| Database | PostgreSQL + SQLAlchemy | Reliable, relational, async support |
| Cache | Redis | Sub-ms aggregates, real-time data |
| Config | Pydantic Settings | Type-safe environment management |
| Dashboard | React + TypeScript | Live charts, KPI cards |
| Containers | Docker + docker-compose | One command to run everything |

---

## Folder Structure
```
cartiq/
├── services/
│   ├── ingestion/            # FastAPI — receives events
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes.py
│   │   │   ├── schemas.py
│   │   │   ├── kafka_producer.py
│   │   │   └── config.py
│   │   └── Dockerfile
│   ├── processor/            # Faust — stream processing
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── agents.py
│   │   │   ├── aggregators.py
│   │   │   └── config.py
│   │   └── Dockerfile
│   └── analytics/            # FastAPI — query API
│       ├── app/
│       │   ├── main.py
│       │   ├── routes.py
│       │   ├── models.py
│       │   ├── schemas.py
│       │   └── config.py
│       └── Dockerfile
├── dashboard/                # React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   └── App.tsx
│   └── package.json
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

---

## Progress Tracker

### Phase 1 — Project Setup ✅
- [x] Create project folder `cartiq/`
- [x] Initialize Poetry
- [x] Add all dependencies
- [x] Create folder structure
- [x] Create `docker-compose.yml` with Kafka, Zookeeper, PostgreSQL, Redis
- [x] Create `.env` file
- [x] Create `.gitignore`

### Phase 2 — Ingestion Service ✅
- [x] `config.py` — Pydantic settings
- [x] `schemas.py` — Event models (product_viewed, cart_added, etc.)
- [x] `kafka_producer.py` — Produce events to Kafka topic
- [x] `routes.py` — POST /events endpoint
- [x] `main.py` — FastAPI app
- [x] Dockerfile for ingestion service
- [x] Test: send events via Swagger UI

### Phase 3 — Stream Processor
- [ ] `config.py` — Kafka + Redis config
- [ ] `agents.py` — Faust agents consuming events
- [ ] `aggregators.py` — Revenue, top products, abandonment rate
- [ ] `main.py` — Faust app entry point
- [ ] Dockerfile for processor
- [ ] Test: verify aggregates appear in Redis

### Phase 4 — Analytics Service
- [ ] `models.py` — SQLAlchemy models for raw events
- [ ] `schemas.py` — Response models
- [ ] `routes.py` — GET /analytics/revenue, /analytics/top-products, etc.
- [ ] `main.py` — FastAPI app
- [ ] Dockerfile for analytics service
- [ ] Test: query analytics via Swagger UI

### Phase 5 — Dashboard
- [ ] Setup React + TypeScript project
- [ ] KPI cards (revenue, active users, failed payments)
- [ ] Live event feed
- [ ] Revenue chart (recharts)
- [ ] Top products chart
- [ ] Auto-refresh every 5 seconds

### Phase 6 — Integration & Polish
- [ ] Full docker-compose with all services
- [ ] Event simulator script (generates fake events for demo)
- [ ] README with architecture diagram
- [ ] `.gitignore`
- [ ] Push to GitHub

---

## Changes Log
> Update this section whenever we change something from the original plan.

| Date | Change | Reason |
|---|---|---|
| 12 May 2026 | Added separate `.env` inside `services/ingestion/` | Local dev uses `localhost:29092`, Docker uses `kafka:9092` |
| 12 May 2026 | Kafka docker-compose updated with two listeners (29092 for local, 9092 for Docker) | Kafka advertises internal hostname, local app can't resolve `kafka:9092` |
| 12 May 2026 | `kafka_producer.py` — lazy producer init + custom datetime serializer | Producer was created before `.env` loaded; datetime not JSON serializable by default |

---

## Resume Line (update as we build)
> "Built CartIQ, a real-time e-commerce analytics pipeline in Python/FastAPI processing events via Apache Kafka, with stream aggregation using Faust, PostgreSQL storage, Redis caching, and a live React dashboard."