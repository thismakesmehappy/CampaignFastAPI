from app.models import User
from app.repositories import user as user_repo
from app.schema import PaginatedFilter
from app.schema.user import UserFilter
from tests.conftest import (
    VALID_USERNAME,
    USER_LIST_USERNAMES,
    LENGTH_OF_USER_RESULTS_DEFAULT,
)


class TestSaveUser:
    async def test_save_user(self, db_session, existing_client, make_user):
        user = await make_user(client_id=existing_client.id)
        assert user.username == VALID_USERNAME
        assert user.client_ids == [existing_client.id]
        assert user.id is not None
        assert user.id > 0

    async def test_save_user_is_admin_defaults_false(self, db_session, existing_client):
        """is_admin has a DB-level default — confirm it lands as False once actually persisted."""
        user = User(username="no_admin_flag_set", password_hash="hash", client_ids=[existing_client.id])
        saved = await user_repo.save(db_session, user)
        assert saved.is_admin is False

    async def test_save_user_update_existing(self, db_session, existing_user):
        existing_user.username = "updated_username"
        user = await user_repo.save(db_session, existing_user)
        assert user.username == "updated_username"
        assert user.id == existing_user.id


class TestGetUser:
    async def test_get_user(self, db_session, existing_user):
        user = await user_repo.get(db_session, existing_user.id)
        assert user is not None
        assert user.id == existing_user.id
        assert user.username == existing_user.username

    async def test_get_user_not_found(self, db_session, existing_user):
        user = await user_repo.get(db_session, existing_user.id + 1)
        assert user is None


class TestGetUserByUsername:
    async def test_get_by_username(self, db_session, existing_user):
        user = await user_repo.get_by_username(db_session, existing_user.username)
        assert user is not None
        assert user.id == existing_user.id

    async def test_get_by_username_not_found(self, db_session, existing_user):
        user = await user_repo.get_by_username(db_session, "no_such_user")
        assert user is None


class TestFindAllUsers:
    async def test_find_all_no_filters(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session)
        assert len(result) == LENGTH_OF_USER_RESULTS_DEFAULT

    async def test_find_all_limit(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session, PaginatedFilter(limit=3))
        assert len(result) == 3

    async def test_find_all_offset_past_end(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session, PaginatedFilter(offset=len(USER_LIST_USERNAMES)))
        assert result == []

    async def test_find_all_empty(self, db_session):
        result = await user_repo.find_all(db_session)
        assert result == []

    async def test_filter_by_username_partial_matches_all(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session, None, UserFilter(username_filter="user_"))
        assert len(result) > 0
        for user in result:
            assert "user_" in user.username.lower()

    async def test_filter_by_username_full_match_returns_one(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session, None, UserFilter(username_filter=USER_LIST_USERNAMES[0]))
        assert len(result) == 1
        assert result[0].username == USER_LIST_USERNAMES[0]

    async def test_filter_by_username_no_match(self, db_session, existing_user_list):
        result = await user_repo.find_all(db_session, None, UserFilter(username_filter="zzznomatch"))
        assert result == []


class TestCountUsers:
    async def test_count_with_entries(self, db_session, existing_user_list):
        total = await user_repo.count(db_session)
        assert total == len(USER_LIST_USERNAMES)

    async def test_count_empty(self, db_session):
        total = await user_repo.count(db_session)
        assert total == 0

    async def test_count_filter_no_match(self, db_session, existing_user_list):
        total = await user_repo.count(db_session, UserFilter(username_filter="zzznomatch"))
        assert total == 0


class TestDeleteUser:
    async def test_delete_user(self, db_session, existing_user):
        await user_repo.delete(db_session, existing_user)
        result = await user_repo.get(db_session, existing_user.id)
        assert result is None
