import logging
import redis
import asyncpg
import json
import time
from datetime import datetime, timedelta
from typing import Optional

from kafka import KafkaAdminClient
import docker
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, HTTPException, Query
from src.config import settings
from common.enums import RedisKey, EventType
from src.schemas import (
    RevenueResponse,
    TopProductsResponse,
    TopProduct,
    EventCountsResponse,
    ActiveUsersResponse,
    DashboardResponse,
    InfraResponse,
    RedisStats,
    KafkaStats,
    KafkaTopicStats,
    SimulatorStatus,
    SimulatorResponse,
)

import docker as docker_sdk

simulator_client = docker_sdk.from_env()

logger = logging.getLogger(__name__)

router = APIRouter()

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)

RESET_TIMESTAMP_KEY = "cartiq:reset:timestamp"


@router.get("/revenue", response_model=RevenueResponse)
async def get_revenue():
    total = redis_client.get(RedisKey.revenue_total)
    return RevenueResponse(total_revenue=float(total or 0))


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products():
    raw = redis_client.zrevrange(RedisKey.top_products, 0, 9, withscores=True)
    products = [
        TopProduct(product_name=name, purchase_count=int(score))
        for name, score in raw
    ]
    return TopProductsResponse(products=products)


@router.get("/event-counts", response_model=EventCountsResponse)
async def get_event_counts():
    def get_count(event_type: EventType) -> int:
        val = redis_client.get(f"cartiq:events:{event_type.value}")
        return int(val or 0)

    total = redis_client.get(RedisKey.events_total)
    return EventCountsResponse(
        product_viewed=get_count(EventType.product_viewed),
        cart_added=get_count(EventType.cart_added),
        cart_removed=get_count(EventType.cart_removed),
        purchase_completed=get_count(EventType.purchase_completed),
        payment_failed=get_count(EventType.payment_failed),
        total=int(total or 0),
    )


@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_active_users():
    five_mins_ago = time.time() - 300
    redis_client.zremrangebyscore(RedisKey.active_users, "-inf", five_mins_ago)
    count = redis_client.zcard(RedisKey.active_users)
    return ActiveUsersResponse(active_users=int(count or 0))


# ── PostgreSQL helpers ─────────────────────────────────────────────

def get_period_start(period: str) -> Optional[datetime]:
    now = datetime.utcnow()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        return now - timedelta(days=7)
    elif period == "month":
        return now - timedelta(days=30)
    elif period == "year":
        return now - timedelta(days=365)
    return None  # all time


async def get_dashboard_from_postgres(period: str) -> DashboardResponse:
    since = get_period_start(period)
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )

    # today → per hour for last 24h
    # week  → per day for last 14 days (current + last week)
    # month → per month for last 24 months
    # year  → per month for current year
    # all   → per month across all data

    if period == "today":
        bucket, fmt, limit = "hour", "%H:00", 24
    elif period == "week":
        bucket, fmt, limit = "day", "%a %d", 14
    elif period == "month":
        bucket, fmt, limit = "month", "%b %Y", 24
    elif period == "year":
        bucket, fmt, limit = "month", "%b %Y", 12
    else:  # all
        bucket, fmt, limit = "month", "%b %Y", 36

    if since:
        total_revenue = await conn.fetchval(
            "SELECT COALESCE(SUM(price * quantity), 0) FROM events WHERE event_type = 'purchase_completed' AND timestamp >= $1", since)
        count_rows = await conn.fetch(
            "SELECT event_type, COUNT(*) FROM events WHERE timestamp >= $1 GROUP BY event_type", since)
        product_rows = await conn.fetch(
            """SELECT product_name, COUNT(*) as cnt FROM events
               WHERE event_type = 'purchase_completed' AND timestamp >= $1
               GROUP BY product_name ORDER BY cnt DESC LIMIT 10""", since)
        history_rows = await conn.fetch(
            f"""SELECT date_trunc('{bucket}', timestamp) as t, SUM(price * quantity) as rev
               FROM events WHERE event_type = 'purchase_completed' AND timestamp >= $1
               GROUP BY t ORDER BY t ASC LIMIT {limit}""", since)
    else:
        total_revenue = await conn.fetchval(
            "SELECT COALESCE(SUM(price * quantity), 0) FROM events WHERE event_type = 'purchase_completed'")
        count_rows = await conn.fetch(
            "SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        product_rows = await conn.fetch(
            """SELECT product_name, COUNT(*) as cnt FROM events
               WHERE event_type = 'purchase_completed'
               GROUP BY product_name ORDER BY cnt DESC LIMIT 10""")
        history_rows = await conn.fetch(
            f"""SELECT date_trunc('{bucket}', timestamp) as t, SUM(price * quantity) as rev
               FROM events WHERE event_type = 'purchase_completed'
               GROUP BY t ORDER BY t ASC LIMIT {limit}""")

    counts = {row["event_type"]: row["count"] for row in count_rows}
    top_products = [TopProduct(product_name=r["product_name"], purchase_count=r["cnt"]) for r in product_rows]
    revenue_history = [{"name": r["t"].strftime(fmt), "revenue": float(r["rev"])} for r in history_rows]

    await conn.close()

    total = sum(counts.values())
    return DashboardResponse(
        revenue=RevenueResponse(total_revenue=float(total_revenue or 0)),
        top_products=TopProductsResponse(products=top_products),
        event_counts=EventCountsResponse(
            product_viewed=counts.get("product_viewed", 0),
            cart_added=counts.get("cart_added", 0),
            cart_removed=counts.get("cart_removed", 0),
            purchase_completed=counts.get("purchase_completed", 0),
            payment_failed=counts.get("payment_failed", 0),
            total=total,
        ),
        active_users=ActiveUsersResponse(active_users=0),
        recent_events=[],
        revenue_history=revenue_history,
    )


# ── Dashboard endpoint ─────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(period: Optional[str] = Query(default=None)):
    if period and period in ("all", "today", "week", "month", "year"):
        return await get_dashboard_from_postgres(period)

    # No period → pure Redis (used for live polling + live session)
    revenue = await get_revenue()
    top_products = await get_top_products()
    event_counts = await get_event_counts()
    active_users = await get_active_users()

    raw_events = redis_client.lrange(RedisKey.recent_events, 0, -1)
    recent_events = [json.loads(e) for e in raw_events] if raw_events else []

    raw_history = redis_client.lrange(RedisKey.revenue_history, 0, -1)
    revenue_history = [json.loads(h) for h in raw_history] if raw_history else []
    revenue_history.reverse()

    return DashboardResponse(
        revenue=revenue,
        top_products=top_products,
        event_counts=event_counts,
        active_users=active_users,
        recent_events=recent_events,
        revenue_history=revenue_history,
    )


# ── Reset endpoint ─────────────────────────────────────────────────

@router.post("/reset")
async def reset_dashboard():
    keys_to_delete = [
        RedisKey.revenue_total,
        RedisKey.top_products,
        RedisKey.active_users,
        RedisKey.events_total,
        RedisKey.recent_events,
        RedisKey.revenue_history,
    ]
    for key in keys_to_delete:
        redis_client.delete(key)

    for event_type in EventType:
        redis_client.delete(f"cartiq:events:{event_type.value}")

    # Store reset timestamp so frontend can show session timer
    redis_client.set(RESET_TIMESTAMP_KEY, str(time.time()))

    logger.info("Dashboard reset: all Redis aggregates cleared")
    return {"status": "reset", "message": "Dashboard cleared.", "reset_at": time.time()}


# ── Session info endpoint ──────────────────────────────────────────

@router.get("/session")
async def get_session():
    """Returns when the last reset happened."""
    ts = redis_client.get(RESET_TIMESTAMP_KEY)
    reset_at = float(ts) if ts else None
    elapsed = int(time.time() - reset_at) if reset_at else None
    return {"reset_at": reset_at, "elapsed_seconds": elapsed}


# ── Infra ──────────────────────────────────────────────────────────

@router.get("/infra", response_model=InfraResponse)
async def get_infra():
    info = redis_client.info()
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    hit_ratio = round(hits / total * 100, 2) if total > 0 else 0.0
    total_keys = sum(v.get("keys", 0) for k, v in info.items() if k.startswith("db"))

    redis_stats = RedisStats(
        used_memory_human=info.get("used_memory_human", "0B"),
        connected_clients=info.get("connected_clients", 0),
        total_commands_processed=info.get("total_commands_processed", 0),
        keyspace_hits=hits,
        keyspace_misses=misses,
        hit_ratio=hit_ratio,
        total_keys=total_keys,
    )

    try:
        admin = KafkaAdminClient(bootstrap_servers=settings.kafka_bootstrap_servers, client_id="cartiq-analytics")
        topic_metadata = admin.list_topics()
        topics = []
        for topic in topic_metadata:
            if not topic.startswith("__"):
                partitions = admin.describe_topics([topic])
                part_count = len(partitions[0].get("partitions", []))
                topics.append(KafkaTopicStats(topic=topic, partitions=part_count, message_count=0))
        admin.close()
    except Exception as e:
        logger.error(f"Kafka admin error: {e}")
        topics = []

    kafka_stats = KafkaStats(bootstrap_servers=settings.kafka_bootstrap_servers, topics=topics, consumer_group="cartiq-processor")
    return InfraResponse(redis=redis_stats, kafka=kafka_stats)


# ── Logs ───────────────────────────────────────────────────────────

def get_container_logs(container_name: str, tail: int = 50):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.logs(stream=True, follow=True, tail=tail, timestamps=True)
    except Exception as e:
        logger.error(f"Docker log error: {e}")
        return None


@router.get("/logs/{service}")
async def stream_logs(service: str):
    container_map = {"redis": "cart_iq-redis-1", "kafka": "cart_iq-kafka-1"}
    if service not in container_map:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    container_name = container_map[service]

    def log_generator():
        logs = get_container_logs(container_name)
        if not logs:
            yield f"data: ERROR: Could not connect to {container_name}\n\n"
            return
        for log in logs:
            line = log.decode("utf-8", errors="replace").strip()
            if line:
                yield f"data: {line}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Simulator ──────────────────────────────────────────────────────

SIMULATOR_CONTAINER_NAMES = ["cart_iq-simulator-1", "cart_iq-simulator"]


def _find_simulator_container():
    """Try to find the simulator container by known names."""
    for name in SIMULATOR_CONTAINER_NAMES:
        try:
            return simulator_client.containers.get(name)
        except docker_sdk.errors.NotFound:
            continue
    return None


@router.post("/simulator/start")
async def start_simulator():
    try:
        container = _find_simulator_container()
        if container:
            if container.status == "running":
                return {"status": "already_running"}
            # Container exists but is stopped/exited — try to restart it
            try:
                container.start()
                return {"status": "started"}
            except Exception:
                # Container is stale (e.g. old network removed) — remove and recreate
                container.remove(force=True)

        # No container (or stale one was removed) — create fresh from the built image
        simulator_client.containers.run(
            "cart_iq-simulator",
            detach=True,
            name="cart_iq-simulator-1",
            environment={
                "INGESTION_URL": "http://ingestion:8000/api/v1/events",
                "REDIS_HOST": "redis",
                "REDIS_PORT": "6379",
                "BATCH_SIZE": "10",
            },
            network="cart_iq_default",
            restart_policy={"Name": "no"},
        )
        return {"status": "started"}
    except docker_sdk.errors.APIError as e:
        # Handle conflict: container name already in use
        if e.status_code == 409:
            try:
                for name in SIMULATOR_CONTAINER_NAMES:
                    try:
                        stale = simulator_client.containers.get(name)
                        stale.remove(force=True)
                    except Exception:
                        pass
                simulator_client.containers.run(
                    "cart_iq-simulator",
                    detach=True,
                    name="cart_iq-simulator-1",
                    environment={
                        "INGESTION_URL": "http://ingestion:8000/api/v1/events",
                        "REDIS_HOST": "redis",
                        "REDIS_PORT": "6379",
                        "BATCH_SIZE": "10",
                    },
                    network="cart_iq_default",
                    restart_policy={"Name": "no"},
                )
                return {"status": "started"}
            except Exception as inner_e:
                raise HTTPException(status_code=500, detail=f"Failed to start after cleanup: {inner_e}")
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/simulator/stop")
async def stop_simulator():
    try:
        container = _find_simulator_container()
        if not container:
            return {"status": "not_found"}
        if container.status != "running":
            return {"status": "not_running"}
        container.stop(timeout=5)
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/simulator/status")
async def simulator_status():
    try:
        container = _find_simulator_container()
        if not container:
            return {"status": "stopped", "is_running": False, "eps": 0}
        is_running = container.status == "running"
        eps = 0
        if is_running:
            try:
                eps = float(redis_client.get("cartiq:simulator:eps") or 0)
            except:
                pass
        return {"status": "running" if is_running else "stopped", "is_running": is_running, "eps": eps}
    except Exception as e:
        return {"status": "unknown", "is_running": False, "eps": 0}


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics"}