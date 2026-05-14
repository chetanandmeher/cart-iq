from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_topic: str = "cartiq_events"
    redis_host: str = "localhost"
    redis_port: int = 6379
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cartiq"
    postgres_user: str = "cartiq_user"
    postgres_password: str = "cartiq_pass"

    class Config:
        env_file = ".env"


settings = Settings()