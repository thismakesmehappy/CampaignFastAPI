import pytest
from pydantic import ValidationError

from app.schema.client import ClientCreate, ClientUpdate, ClientFilter, ClientRead
from app.constants import CAMPAIGN_NAME_MAX_LENGTH

VALID_NAME = "Acme Corp"
VALID_API_KEY = "secret-key-123"
VALID_EMAIL = "contact@acme.com"


class TestClientCreate:
    def test_valid_minimal(self):
        client = ClientCreate(name=VALID_NAME, api_key=VALID_API_KEY)
        assert client.name == VALID_NAME
        assert client.api_key == VALID_API_KEY
        assert client.email is None
        assert client.notes is None
        assert client.is_active is True

    def test_valid_full(self):
        client = ClientCreate(name=VALID_NAME, api_key=VALID_API_KEY, email=VALID_EMAIL, notes="VIP", is_active=False)
        assert client.email == VALID_EMAIL
        assert client.notes == "VIP"
        assert client.is_active is False

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ClientCreate(name="A" * (CAMPAIGN_NAME_MAX_LENGTH + 1), api_key=VALID_API_KEY)

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ClientCreate(name="", api_key=VALID_API_KEY)

    def test_api_key_empty(self):
        with pytest.raises(ValidationError):
            ClientCreate(name=VALID_NAME, api_key="")

    def test_name_missing(self):
        with pytest.raises(ValidationError):
            ClientCreate(api_key=VALID_API_KEY)

    def test_api_key_missing(self):
        with pytest.raises(ValidationError):
            ClientCreate(name=VALID_NAME)


class TestClientUpdate:
    def test_all_none(self):
        update = ClientUpdate()
        assert update.name is None
        assert update.email is None
        assert update.notes is None
        assert update.is_active is None

    def test_partial_update(self):
        update = ClientUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.is_active is None

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ClientUpdate(name="A" * (CAMPAIGN_NAME_MAX_LENGTH + 1))


class TestClientFilter:
    def test_defaults_empty(self):
        f = ClientFilter()
        assert f.name_filter == ""

    def test_name_filter(self):
        f = ClientFilter(name_filter="acme")
        assert f.name_filter == "acme"


class TestClientRead:
    def test_from_attributes(self):
        from datetime import datetime

        class FakeOrm:
            id = 1
            name = VALID_NAME
            email = VALID_EMAIL
            notes = None
            is_active = True
            created_at = datetime(2025, 1, 1)

        read = ClientRead.model_validate(FakeOrm())
        assert read.id == 1
        assert read.name == VALID_NAME
        assert read.email == VALID_EMAIL
        assert read.is_active is True

    def test_api_key_not_exposed(self):
        fields = ClientRead.model_fields
        assert "api_key" not in fields