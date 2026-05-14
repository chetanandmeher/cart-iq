"""
CartIQ — Event Simulator
Sends randomized e-commerce events to the Ingestion API in a loop.
Run this to populate the dashboard with live data.

Usage:
    python scripts/simulate_events.py
"""

import requests
import random
import time
import uuid
from datetime import datetime, timezone

INGESTION_URL = "http://localhost:8001/api/v1/events"

PRODUCTS = [
    {"name": "iPhone 15 Pro", "price": 134900},
    {"name": "Samsung Galaxy S24", "price": 79999},
    {"name": "Sony WH-1000XM5", "price": 29990},
    {"name": "MacBook Air M3", "price": 114900},
    {"name": "Nike Air Max 270", "price": 9995},
    {"name": "Levi's 501 Jeans", "price": 4999},
    {"name": "Kindle Paperwhite", "price": 13999},
    {"name": "Boat Airdopes 141", "price": 1299},
    {"name": "OnePlus 12R", "price": 39999},
    {"name": "Canon EOS R50", "price": 64995},
]

EVENT_TYPES = [
    "product_viewed",   # most frequent
    "product_viewed",
    "product_viewed",
    "cart_added",       # medium
    "cart_added",
    "cart_removed",     # occasional
    "purchase_completed",  # less frequent
    "payment_failed",   # rare
]

USER_IDS = [f"user_{i:04d}" for i in range(1, 51)]  # 50 simulated users


def make_event(event_type: str, product: dict, user_id: str) -> dict:
    base = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": user_id,
        "session_id": str(uuid.uuid4()),
        "product_id": str(uuid.uuid4()),
        "product_name": product["name"],
        "price": product["price"],
        "quantity": random.randint(1, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return base


def send_event(event: dict) -> bool:
    try:
        response = requests.post(INGESTION_URL, json=event, timeout=3)
        if response.status_code == 202:
            print(f"  ✅  [{event['event_type']:25s}]  {event['product_name']}  (user: {event['user_id']})")
            return True
        else:
            print(f"  ❌  HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌  Cannot connect to Ingestion API at http://localhost:8001")
        print("      Make sure the ingestion service is running.")
        return False
    except Exception as e:
        print(f"  ❌  Error: {e}")
        return False


def main():
    print("=" * 60)
    print("  CartIQ Event Simulator")
    print("  Sending events to:", INGESTION_URL)
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    total_sent = 0
    total_failed = 0

    try:
        while True:
            event_type = random.choice(EVENT_TYPES)
            product = random.choice(PRODUCTS)
            user_id = random.choice(USER_IDS)

            event = make_event(event_type, product, user_id)
            success = send_event(event)

            if success:
                total_sent += 1
            else:
                total_failed += 1

            # High speed delay: 0.01s to 0.1s between events
            delay = random.uniform(0.01, 0.1)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"  Simulator stopped.")
        print(f"  Events sent:   {total_sent}")
        print(f"  Events failed: {total_failed}")
        print("=" * 60)


if __name__ == "__main__":
    main()
