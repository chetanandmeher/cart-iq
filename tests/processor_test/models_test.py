"""
Tests for the SQLAlchemy Event model.
"""
from src.models import Event, Base


class TestEventModel:
    def test_tablename(self):
        assert Event.__tablename__ == "events"

    def test_has_all_columns(self):
        column_names = {col.name for col in Event.__table__.columns}
        expected = {
            "event_id",
            "event_type",
            "user_id",
            "product_id",
            "product_name",
            "price",
            "quantity",
            "timestamp",
            "extra_data",
        }
        assert expected == column_names

    def test_primary_key_is_event_id(self):
        pk_columns = [col.name for col in Event.__table__.primary_key.columns]
        assert pk_columns == ["event_id"]

    def test_event_type_is_indexed(self):
        col = Event.__table__.columns["event_type"]
        assert col.index is True

    def test_user_id_is_indexed(self):
        col = Event.__table__.columns["user_id"]
        assert col.index is True

    def test_timestamp_is_indexed(self):
        col = Event.__table__.columns["timestamp"]
        assert col.index is True

    def test_event_type_not_nullable(self):
        col = Event.__table__.columns["event_type"]
        assert col.nullable is False

    def test_user_id_not_nullable(self):
        col = Event.__table__.columns["user_id"]
        assert col.nullable is False

    def test_product_id_not_nullable(self):
        col = Event.__table__.columns["product_id"]
        assert col.nullable is False

    def test_price_not_nullable(self):
        col = Event.__table__.columns["price"]
        assert col.nullable is False

    def test_extra_data_is_nullable(self):
        col = Event.__table__.columns["extra_data"]
        assert col.nullable is True

    def test_quantity_default_is_one(self):
        col = Event.__table__.columns["quantity"]
        assert col.default.arg == 1

    def test_inherits_from_base(self):
        assert issubclass(Event, Base)
