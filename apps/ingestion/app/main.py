import logging
from fastapi import FastAPI
from app.routes import router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="CartIQ Ingestion Service",
    description="Receives e-commerce events and publishes to Kafka",
    version="1.0.0",
    debug=settings.debug
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logging.info("Ingestion service started")


@app.on_event("shutdown")
async def shutdown():
    logging.info("Ingestion service shutting down")