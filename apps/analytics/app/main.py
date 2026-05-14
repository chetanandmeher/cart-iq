import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="CartIQ Analytics API",
    description="Real-time e-commerce analytics powered by Redis",
    version="1.0.0",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/analytics")


@app.on_event("startup")
async def startup():
    logging.info("Analytics service started")


@app.on_event("shutdown")
async def shutdown():
    logging.info("Analytics service shutting down")