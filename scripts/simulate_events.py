"""
CartIQ — Mega-Scale Batched Simulator
Simulates massive traffic with STABLE product IDs and realistic names.
"""

import requests
import random
import time
import uuid
import threading
import queue
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

INGESTION_URL = "http://localhost:8001/api/v1/events"
BATCH_SIZE = 50 
event_queue = queue.Queue()

# Stable Product Pool
PRODUCT_NAMES = [
    "iPhone 15 Pro", "Samsung Galaxy S24", "Sony WH-1000XM5", "MacBook Air M3",
    "iPad Pro 12.9", "Nintendo Switch OLED", "DJI Mini 4 Pro", "Kindle Paperwhite",
    "Logitech MX Master 3S", "AirPods Pro 2", "GoPro HERO12", "PlayStation 5",
    "Xbox Series X", "Dell XPS 13", "Bose QuietComfort Ultra", "Canon EOS R50",
    "Apple Watch Ultra 2", "Samsung Odyssey G9", "Razer BlackWidow V4", "Steam Deck"
]

# Create 100 stable products
PRODUCTS = []
for i in range(100):
    base_name = PRODUCT_NAMES[i % len(PRODUCT_NAMES)]
    suffix = f" (Gen {i // len(PRODUCT_NAMES) + 1})" if i >= len(PRODUCT_NAMES) else ""
    PRODUCTS.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"product_{i}")),
        "name": f"{base_name}{suffix}",
        "price": random.randint(2000, 150000)
    })

# Scale up users (1000 active users)
USER_IDS = [f"user_{i:04d}" for i in range(1, 1001)]

def make_event(event_type: str, product: dict, user_id: str) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": user_id,
        "session_id": str(uuid.uuid4()),
        "product_id": product["id"], # STABLE ID
        "product_name": product["name"], # REAL NAME
        "price": product["price"],
        "quantity": random.randint(1, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def batch_sender():
    """Worker thread that pulls events from queue and sends in batches."""
    print(f"📡 Batch sender started (Batch Size: {BATCH_SIZE})")
    while True:
        batch = []
        try:
            while len(batch) < BATCH_SIZE:
                timeout = 1.0 if not batch else 0.05
                try:
                    event = event_queue.get(timeout=timeout)
                    batch.append(event)
                except queue.Empty:
                    break
            
            if batch:
                try:
                    res = requests.post(INGESTION_URL, json=batch, timeout=10)
                    if res.status_code == 202:
                        # Batch processed
                        pass
                    else:
                        print(f"  ❌ Batch Failed: {res.status_code}")
                except Exception as e:
                    print(f"  ❌ Network Error: {e}")
                finally:
                    for _ in range(len(batch)):
                        event_queue.task_done()
        except Exception as e:
            print(f"  ⚠️ Sender Error: {e}")

def simulate_user_journey():
    """Virtual customer producing events into the global queue."""
    while True:
        user_id = random.choice(USER_IDS)
        # 1. View some products
        for _ in range(random.randint(2, 6)):
            product = random.choice(PRODUCTS)
            event_queue.put(make_event("product_viewed", product, user_id))
            time.sleep(random.uniform(0.01, 0.05))

        # 2. Maybe add to cart
        if random.random() < 0.7:
            product = random.choice(PRODUCTS)
            event_queue.put(make_event("cart_added", product, user_id))
            time.sleep(random.uniform(0.05, 0.1))

            # 3. Maybe purchase
            if random.random() < 0.5:
                event_queue.put(make_event("purchase_completed", product, user_id))
        
        time.sleep(random.uniform(0.05, 0.2))

def main():
    num_threads = 20
    print(f"🔥 Starting CartIQ Mega-Scale BATCHED Simulator...")
    print(f"📦 Product Pool: {len(PRODUCTS)} stable products")
    
    sender = threading.Thread(target=batch_sender, daemon=True)
    sender.start()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            executor.submit(simulate_user_journey)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped.")
