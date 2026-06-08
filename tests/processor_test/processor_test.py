"""
Tests for processor config settings.
"""
from src.config import Settings


class TestProcessorConfig:
    def test_kafka_topic_default(self):
        s = Settings()
        assert s.kafka_topic == "cartiq_events"

    def test_redis_defaults(self):
        s = Settings()
        assert s.redis_host == "localhost"
        assert s.redis_port == 6379

    def test_postgres_defaults(self):
        s = Settings()
        assert s.postgres_host == "localhost"
        assert s.postgres_port == 5432
        assert s.postgres_db == "cartiq"
        assert s.postgres_user == "cartiq_user"
        assert s.postgres_password == "cartiq_pass"

    def test_kafka_bootstrap_default(self):
        s = Settings()
        assert s.kafka_bootstrap_servers == "localhost:29092"

    def test_all_fields_present(self):
        """Verify no field was accidentally removed."""
        s = Settings()
        expected_fields = {
            "kafka_bootstrap_servers",
            "kafka_topic",
            "redis_host",
            "redis_port",
            "postgres_host",
            "postgres_port",
            "postgres_db",
            "postgres_user",
            "postgres_password",
        }
        actual_fields = set(s.model_fields.keys())
        assert expected_fields.issubset(actual_fields)
