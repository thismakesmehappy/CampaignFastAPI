import pytest

from app.services import user as user_service
from app.services.user import pwd_context
from app.schema.user import UserCreate, UserUpdate, UserFilter, LoginRequest
from app.schema import PaginatedFilter
from app.exceptions import NotFoundError, DomainValidationError
from tests.conftest import VALID_USERNAME, VALID_PASSWORD, USER_LIST_USERNAMES


class TestCreateUser:
    async def test_create_user(self, db_session, existing_client):
        data = UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=[existing_client.id])
        user = await user_service.create(db_session, data)
        assert user.id is not None
        assert user.username == VALID_USERNAME
        assert user.client_ids == [existing_client.id]

    async def test_create_user_hashes_password(self, db_session, existing_client):
        data = UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=[existing_client.id])
        user = await user_service.create(db_session, data)
        assert user.password_hash != VALID_PASSWORD
        assert pwd_context.verify(VALID_PASSWORD, user.password_hash)

    async def test_create_user_client_not_found(self, db_session):
        data = UserCreate(username=VALID_USERNAME, password=VALID_PASSWORD, client_ids=[999999999999])
        with pytest.raises(NotFoundError):
            await user_service.create(db_session, data)


class TestGetUser:
    async def test_get_user(self, db_session, existing_user):
        user = await user_service.get(db_session, existing_user.id)
        assert user.id == existing_user.id

    async def test_get_user_not_found(self, db_session, existing_user):
        with pytest.raises(NotFoundError):
            await user_service.get(db_session, existing_user.id + 1)


class TestListUsers:
    async def test_list_users(self, db_session, existing_user_list):
        result = await user_service.list_users(db_session)
        assert result.total == len(USER_LIST_USERNAMES)

    async def test_list_users_pagination(self, db_session, existing_user_list):
        result = await user_service.list_users(db_session, PaginatedFilter(limit=3))
        assert len(result.items) == 3

    async def test_list_users_filter_by_username(self, db_session, existing_user_list):
        result = await user_service.list_users(db_session, options=UserFilter(username_filter=USER_LIST_USERNAMES[0]))
        assert result.total == 1
        assert result.items[0].username == USER_LIST_USERNAMES[0]

    async def test_list_users_empty(self, db_session):
        result = await user_service.list_users(db_session)
        assert result.total == 0
        assert result.items == []

    async def test_list_users_filter_by_ids_not_found(self, db_session, existing_user_list):
        with pytest.raises(NotFoundError):
            await user_service.list_users(db_session, options=UserFilter(ids="999999999999"))


class TestUpdateUser:
    async def test_update_username(self, db_session, existing_user):
        result = await user_service.update(db_session, existing_user.id, UserUpdate(username="new_username"))
        assert result.username == "new_username"

    async def test_update_password_rehashes(self, db_session, existing_user):
        old_hash = existing_user.password_hash
        result = await user_service.update(db_session, existing_user.id, UserUpdate(password="new-password-123"))
        assert result.password_hash != old_hash
        assert pwd_context.verify("new-password-123", result.password_hash)

    async def test_update_client_ids(self, db_session, existing_user, existing_client):
        from app.repositories import client as client_repo
        from app.models import Client
        other_client = await client_repo.save(db_session, Client(name="Other Client", api_key="other-key"))
        result = await user_service.update(db_session, existing_user.id, UserUpdate(client_ids=[other_client.id]))
        assert result.client_ids == [other_client.id]

    async def test_update_client_ids_not_found(self, db_session, existing_user):
        with pytest.raises(NotFoundError):
            await user_service.update(db_session, existing_user.id, UserUpdate(client_ids=[999999999999]))

    async def test_update_not_found(self, db_session, existing_user):
        with pytest.raises(NotFoundError):
            await user_service.update(db_session, existing_user.id + 1, UserUpdate(username="x"))


class TestDeleteUser:
    async def test_delete_user(self, db_session, existing_user):
        await user_service.delete(db_session, existing_user.id)
        with pytest.raises(NotFoundError):
            await user_service.get(db_session, existing_user.id)

    async def test_delete_user_not_found(self, db_session, existing_user):
        with pytest.raises(NotFoundError):
            await user_service.delete(db_session, existing_user.id + 1)


class TestLogin:
    async def test_login_success(self, db_session, existing_client, make_user):
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)
        result = await user_service.login(db_session, LoginRequest(username=VALID_USERNAME, password=VALID_PASSWORD))
        assert len(result.clients) == 1
        assert result.clients[0].client_id == existing_client.id
        assert result.clients[0].client_name == existing_client.name

    async def test_login_wrong_password(self, db_session, existing_client, make_user):
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)
        with pytest.raises(DomainValidationError):
            await user_service.login(db_session, LoginRequest(username=VALID_USERNAME, password="wrong-password"))

    async def test_login_unknown_username(self, db_session):
        with pytest.raises(DomainValidationError):
            await user_service.login(db_session, LoginRequest(username="no_such_user", password="whatever"))

    async def test_login_error_message_same_for_bad_username_and_bad_password(self, db_session, existing_client, make_user):
        """The login error message must not reveal whether the username or password was wrong (no user enumeration)."""
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)

        with pytest.raises(DomainValidationError) as bad_password_exc:
            await user_service.login(db_session, LoginRequest(username=VALID_USERNAME, password="wrong-password"))

        with pytest.raises(DomainValidationError) as bad_username_exc:
            await user_service.login(db_session, LoginRequest(username="no_such_user", password="whatever"))

        assert bad_password_exc.value.messages == bad_username_exc.value.messages