from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "cartiq_events"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()