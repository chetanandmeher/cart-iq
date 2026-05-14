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

### Phase 3 — Stream Processor ✅
- [x] `config.py` — Kafka + Redis config
- [x] `enums.py` — EventType and RedisKey enums
- [x] `agents.py` — Faust agents consuming events
- [x] `aggregators.py` — Revenue, top products, event counts, active users
- [x] `main.py` — Faust app entry point
- [ ] Dockerfile for processor
- [x] Test: verify aggregates appear in Redis

### Phase 4 — Analytics Service ✅
- [x] `enums.py` — EventType and RedisKey enums
- [x] `schemas.py` — Response models
- [x] `routes.py` — GET /analytics/revenue, /analytics/top-products, etc.
- [x] `main.py` — FastAPI app
- [ ] Dockerfile for analytics service
- [x] Test: query analytics via Swagger UI

### Phase 5 — Dashboard ✅
- [x] Setup React + TypeScript project (Vite + Tailwind + Framer Motion + Recharts)
- [x] KPI cards (revenue, active users, total orders, failed payments)
- [x] Live event feed (served by backend Redis list `recent_events`)
- [x] Revenue area chart (Recharts, backed by backend `revenue_history`)
- [x] Top products bar chart + Event breakdown pie chart
- [x] Auto-refresh every 5 seconds
- [x] Sidebar + TopBar navigation shell
- [x] Glassmorphism dark-mode design system (TailwindCSS)
- [x] Error state + Loading state handling

### Phase 6 — Integration & Polish
- [x] Full docker-compose with all services (Kafka, Zookeeper, PG, Redis, Ingestion, Processor, Analytics)
- [x] Dockerfile for `services/processor`
- [x] Dockerfile for `services/analytics`
- [x] Event simulator script (generates fake events for demo)
- [x] Fix pie chart hardcoded center text (`18k` → real total)
- [x] README with architecture diagram
- [x] `.gitignore`
- [x] Push to GitHub

---

## Changes Log
> Update this section whenever we change something from the original plan.

| Date | Change | Reason |
|---|---|---|
| 12 May 2026 | Added separate `.env` inside `services/ingestion/` | Local dev uses `localhost:29092`, Docker uses `kafka:9092` |
| 12 May 2026 | Kafka docker-compose updated with two listeners (29092 for local, 9092 for Docker) | Kafka advertises internal hostname, local app can't resolve `kafka:9092` |
| 12 May 2026 | `kafka_producer.py` — lazy producer init + custom datetime serializer | Producer was created before `.env` loaded; datetime not JSON serializable by default |
| 14 May 2026 | Dashboard rebuilt from scratch using Vite + React 19 + TailwindCSS | Replaced old dashboard; new design uses glassmorphism dark-mode theme |
| 14 May 2026 | Dashboard polls `GET /api/v1/analytics/dashboard` every 5s | Single aggregated endpoint is more efficient than 4 separate calls |
| 14 May 2026 | Live feed uses diff-based detection (ref vs current counts) | Avoids fake event generation; reflects real backend changes |
| 14 May 2026 | Analytics API CORS updated to allow `http://localhost:5173` | Required for local dev dashboard to call the backend without CORS errors |
| 14 May 2026 | Moved Live Feed & Revenue History to Backend | Frontend was doing synthetic diffs; processor now tracks `recent_events` and `revenue_history` in Redis to support page reloads. |

---

## Resume Line (update as we build)
> "Built CartIQ, a real-time e-commerce analytics pipeline in Python/FastAPI processing events via Apache Kafka, with stream aggregation using Faust, PostgreSQL storage, Redis caching, and a live React dashboard."