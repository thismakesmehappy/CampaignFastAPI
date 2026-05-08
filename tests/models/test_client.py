import pytest

from app.models.client import Client
from app.constants import CAMPAIGN_NAME_MAX_LENGTH

VALID_NAME = "Acme Corp"
VALID_EMAIL = "contact@acme.com"
VALID_API_KEY = "secret-key-123"
LONG_NAME = "A" * (CAMPAIGN_NAME_MAX_LENGTH + 1)
MAX_NAME = "A" * CAMPAIGN_NAME_MAX_LENGTH


class TestClientModel:
    def test_valid_client(self):
        client = Client(name=VALID_NAME, api_key=VALID_API_KEY)
        assert client.name == VALID_NAME
        assert client.api_key == VALID_API_KEY

    def test_name_at_max_length(self):
        client = Client(name=MAX_NAME, api_key=VALID_API_KEY)
        assert client.name == MAX_NAME

    def test_name_too_long(self):
        with pytest.raises(ValueError):
            Client(name=LONG_NAME, api_key=VALID_API_KEY)

    def test_name_none(self):
        with pytest.raises(ValueError):
            Client(name=None, api_key=VALID_API_KEY)

    def test_email_optional(self):
        client = Client(name=VALID_NAME, api_key=VALID_API_KEY, email=None)
        assert client.email is None

    def test_valid_email(self):
        client = Client(name=VALID_NAME, api_key=VALID_API_KEY, email=VALID_EMAIL)
        assert client.email == VALID_EMAIL

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            Client(name=VALID_NAME, api_key=VALID_API_KEY, email="not-an-email")

    def test_invalid_email_missing_domain(self):
        with pytest.raises(ValueError):
            Client(name=VALID_NAME, api_key=VALID_API_KEY, email="user@")

    def test_is_active_can_be_set(self):
        client = Client(name=VALID_NAME, api_key=VALID_API_KEY, is_active=False)
        assert client.is_active is False

    def test_notes_optional(self):
        client = Client(name=VALID_NAME, api_key=VALID_API_KEY, notes="some notes")
        assert client.notes == "some notes"