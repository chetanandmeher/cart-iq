"""
CartIQ — High-Scale Event Simulator
Simulates thousands of concurrent virtual customers on a large e-commerce platform.
Uses multi-threading to stress-test the ingestion and processing pipeline.
"""

import requests
import random
import time
import uuid
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

INGESTION_URL = "http://localhost:8001/api/v1/events"

# Scale up products (100 products)
PRODUCTS = [
    {"name": f"Product {i:03d}", "price": random.randint(500, 150000)}
    for i in range(1, 101)
]

# Scale up users (1000 active users)
USER_IDS = [f"user_{i:04d}" for i in range(1, 1001)]

EVENT_TYPES = [
    "product_viewed",
    "cart_added",
    "cart_removed",
    "purchase_completed",
    "payment_failed",
]

def make_event(event_type: str, product: dict, user_id: str) -> dict:
    return {
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

def send_event(event: dict):
    try:
        response = requests.post(INGESTION_URL, json=event, timeout=5)
        if response.status_code == 202:
            print(f"  ✅  [{event['event_type']:18s}] {event['product_name']:20s} (user: {event['user_id']})")
            return True
        return False
    except:
        return False

def simulate_user_journey():
    """Simulates a single user's path through the site, then picks a new user."""
    while True:
        user_id = random.choice(USER_IDS)
        # 1. View some products
        for _ in range(random.randint(1, 3)):
            product = random.choice(PRODUCTS)
            send_event(make_event("product_viewed", product, user_id))
            time.sleep(random.uniform(0.05, 0.2))

        # 2. Maybe add to cart
        if random.random() < 0.6:
            product = random.choice(PRODUCTS)
            send_event(make_event("cart_added", product, user_id))
            time.sleep(random.uniform(0.1, 0.3))

            # 3. Maybe purchase
            if random.random() < 0.4:
                send_event(make_event("purchase_completed", product, user_id))
        
        # User 'leaves' the site, next iteration will pick a new user_id
        time.sleep(random.uniform(0.1, 0.5))

def main():
    # Increase to 50 concurrent threads (virtual customers)
    num_threads = 50 
    print(f"🚀 Starting CartIQ Mega-Scale Simulator with {num_threads} threads...")
    print(f"📍 Target: {INGESTION_URL}")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            executor.submit(simulate_user_journey)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped.")
