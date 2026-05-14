import logging
import redis

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
import docker
from fastapi.responses import StreamingResponse
import time


from fastapi import APIRouter, HTTPException
from app.config import settings
from app.enums import RedisKey, EventType
from app.schemas import (
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
    # 1. Clean up old users (sliding 5-minute window)
    import time
    five_mins_ago = time.time() - 300
    redis_client.zremrangebyscore(RedisKey.active_users, "-inf", five_mins_ago)
    
    # 2. Get the count of remaining unique users
    count = redis_client.zcard(RedisKey.active_users)
    return ActiveUsersResponse(active_users=int(count or 0))


import json

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
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
@router.get("/infra", response_model=InfraResponse)
async def get_infra():
    # Redis stats
    info = redis_client.info()
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    hit_ratio = round(hits / total * 100, 2) if total > 0 else 0.0
    total_keys = sum(
        v.get("keys", 0)
        for k, v in info.items()
        if k.startswith("db")
    )

    redis_stats = RedisStats(
        used_memory_human=info.get("used_memory_human", "0B"),
        connected_clients=info.get("connected_clients", 0),
        total_commands_processed=info.get("total_commands_processed", 0),
        keyspace_hits=hits,
        keyspace_misses=misses,
        hit_ratio=hit_ratio,
        total_keys=total_keys,
    )

    # Kafka stats
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id="cartiq-analytics"
        )
        topic_metadata = admin.list_topics()
        topics = []
        for topic in topic_metadata:
            if not topic.startswith("__"):
                partitions = admin.describe_topics([topic])
                part_count = len(partitions[0].get("partitions", []))
                topics.append(KafkaTopicStats(
                    topic=topic,
                    partitions=part_count,
                    message_count=0
                ))
        admin.close()
    except Exception as e:
        logger.error(f"Kafka admin error: {e}")
        topics = []

    kafka_stats = KafkaStats(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topics=topics,
        consumer_group="cartiq-processor"
    )

    return InfraResponse(redis=redis_stats, kafka=kafka_stats)


def get_container_logs(container_name: str, tail: int = 50):
    """Stream logs from a Docker container."""
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        logs = container.logs(stream=True, follow=True, tail=tail, timestamps=True)
        return logs
    except Exception as e:
        logger.error(f"Docker log error: {e}")
        return None


@router.get("/logs/{service}")
async def stream_logs(service: str):
    """Stream logs from Redis or Kafka container via SSE."""
    container_map = {
        "redis": "cart_iq-redis-1",
        "kafka": "cart_iq-kafka-1",
    }

    if service not in container_map:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}. Use 'redis' or 'kafka'")

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

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/simulator/start")
async def start_simulator():
    try:
        container = simulator_client.containers.get("cart_iq-simulator")
        if container.status == "running":
            return {"status": "already_running"}
        container.start()
        return {"status": "started"}
    except docker_sdk.errors.NotFound:
        try:
            simulator_client.containers.run(
                "cart_iq-simulator",  # image name
                detach=True,
                name="cart_iq-simulator",
                environment={
                    "INGESTION_URL": "http://ingestion:8000/api/v1/events"
                },
                network="cart_iq_default",
                remove=False,
            )
            return {"status": "started"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/simulator/stop")
async def stop_simulator():
    try:
        container = simulator_client.containers.get("cart_iq-simulator")
        if container.status != "running":
            return {"status": "not_running"}
        container.stop(timeout=5)
        return {"status": "stopped"}
    except docker_sdk.errors.NotFound:
        return {"status": "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

while
@router.get("/simulator/status")
async def simulator_status():
    global simulator_process
    try:
        container = simulator_client.containers.get("cart_iq-simulator")
        is_running = container.status == "running"
        eps = 0
        if is_running:
            try:
                eps = float(redis_client.get("cartiq:simulator:eps") or 0)
            except:
                pass
        return {
            "status": "running" if is_running else "stopped",
            "is_running": is_running,
            "eps": eps
        }
    except docker_sdk.errors.NotFound:
        return {"status": "stopped", "is_running": False, "eps": 0}
    except Exception as e:
        return {"status": "unknown", "is_running": False, "eps": 0}


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics"}