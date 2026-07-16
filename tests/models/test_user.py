import pytest

from app.models.user import User

VALID_USERNAME = "acme_demo"
VALID_PASSWORD_HASH = "$2b$12$fakehashfaketestingonly"
VALID_CLIENT_IDS = [1]
LONG_USERNAME = "A" * 101
MAX_USERNAME = "A" * 100


class TestUserModel:
    def test_valid_user(self):
        user = User(username=VALID_USERNAME, password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)
        assert user.username == VALID_USERNAME
        assert user.password_hash == VALID_PASSWORD_HASH
        assert user.client_ids == VALID_CLIENT_IDS

    def test_is_admin_not_set_on_bare_construction(self):
        """default=False is a DB-level default applied on INSERT, not a Python default — see repository test for the persisted-default behavior."""
        user = User(username=VALID_USERNAME, password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)
        assert user.is_admin is None

    def test_username_at_max_length(self):
        user = User(username=MAX_USERNAME, password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)
        assert user.username == MAX_USERNAME

    def test_username_too_long(self):
        with pytest.raises(ValueError):
            User(username=LONG_USERNAME, password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)

    def test_username_none(self):
        with pytest.raises(ValueError):
            User(username=None, password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)

    def test_username_empty(self):
        with pytest.raises(ValueError):
            User(username="", password_hash=VALID_PASSWORD_HASH, client_ids=VALID_CLIENT_IDS)
