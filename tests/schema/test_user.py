import pytest
from pydantic import ValidationError

from app.schema.user import UserCreate, UserUpdate, UserFilter, UserRead, LoginRequest, LoginResponse, LoginClient

VALID_USERNAME = "acme_demo"
VALID_PASSWORD = "test-password-123"
VALID_CLIENT_IDS = [1]


class TestUserCreate:
    def test_valid(self):
        user = UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=VALID_CLIENT_IDS)
        assert user.username == VALID_USERNAME
        assert user.password == VALID_PASSWORD
        assert user.client_ids == VALID_CLIENT_IDS

    def test_username_empty(self):
        with pytest.raises(ValidationError):
            UserCreate(username="", password=VALID_PASSWORD, client_ids=VALID_CLIENT_IDS)

    def test_username_missing(self):
        with pytest.raises(ValidationError):
            UserCreate(password=VALID_PASSWORD, client_ids=VALID_CLIENT_IDS)

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username=VALID_USERNAME, password="short", client_ids=VALID_CLIENT_IDS)

    def test_password_missing(self):
        with pytest.raises(ValidationError):
            UserCreate(username=VALID_USERNAME, client_ids=VALID_CLIENT_IDS)

    def test_client_ids_missing(self):
        with pytest.raises(ValidationError):
            UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD)

    def test_client_ids_empty(self):
        with pytest.raises(ValidationError):
            UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=[])

    def test_client_ids_more_than_one_rejected(self):
        """Array-shaped for a future many-to-many move, but only one client is supported today."""
        with pytest.raises(ValidationError):
            UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=[1, 2])


class TestUserUpdate:
    def test_all_none(self):
        update = UserUpdate()
        assert update.username is None
        assert update.password is None
        assert update.client_ids is None

    def test_partial_update(self):
        update = UserUpdate(username="new_name")
        assert update.username == "new_name"
        assert update.password is None

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserUpdate(password="short")

    def test_client_ids_more_than_one_rejected(self):
        with pytest.raises(ValidationError):
            UserUpdate(client_ids=[1, 2])


class TestUserFilter:
    def test_defaults_empty(self):
        f = UserFilter()
        assert f.username_filter == ""
        assert f.id_list == []

    def test_username_filter(self):
        f = UserFilter(username_filter="acme")
        assert f.username_filter == "acme"

    def test_id_list_parses_csv(self):
        f = UserFilter(ids="1,2,3")
        assert f.id_list == [1, 2, 3]


class TestUserRead:
    def test_from_attributes(self):
        from datetime import datetime

        class FakeOrm:
            id = 1
            username = VALID_USERNAME
            password_hash = "should-never-be-read"
            client_ids = VALID_CLIENT_IDS
            is_admin = False
            created_at = datetime(2026, 1, 1)

        read = UserRead.model_validate(FakeOrm())
        assert read.id == 1
        assert read.username == VALID_USERNAME
        assert read.client_ids == VALID_CLIENT_IDS

    def test_password_hash_not_exposed(self):
        fields = UserRead.model_fields
        assert "password_hash" not in fields
        assert "password" not in fields

    def test_is_admin_not_exposed(self):
        """is_admin exists on the model but isn't wired into any schema/endpoint yet — future admin-path work."""
        fields = UserRead.model_fields
        assert "is_admin" not in fields


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(username=VALID_USERNAME, password=VALID_PASSWORD)
        assert req.username == VALID_USERNAME
        assert req.password == VALID_PASSWORD


class TestLoginResponse:
    def test_valid(self):
        res = LoginResponse(clients=[LoginClient(client_id=1, client_name="Acme Corp")])
        assert len(res.clients) == 1
        assert res.clients[0].client_id == 1
        assert res.clients[0].client_name == "Acme Corp"

    def test_no_token_field(self):
        fields = LoginResponse.model_fields
        assert "token" not in fields

    def test_clients_is_a_list(self):
        fields = LoginResponse.model_fields
        assert "clients" in fields