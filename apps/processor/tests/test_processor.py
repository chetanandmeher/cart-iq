from src.config import settings

def test_config():
    assert settings.kafka_topic == "cartiq_events"
