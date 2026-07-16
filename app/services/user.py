from passlib.context import CryptContext

from app.repositories import user as user_repo
from app.repositories import client as client_repo
from app.exceptions import NotFoundError, DomainValidationError
from app.models import User
from app.schema import PaginatedFilter, PaginatedResponse
from app.schema.user import UserCreate, UserUpdate, UserFilter, LoginRequest, LoginResponse, LoginClient

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def _get_client_or_raise(db, client_id: int):
    client = await client_repo.get(db, client_id)
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()
    return client


def _build_user(data: UserCreate) -> User:
    try:
        return User(
            username=data.username,
            password_hash=pwd_context.hash(data.password),
            client_ids=data.client_ids,
        )
    except ValueError as e:
        err = DomainValidationError()
        err.capture(str(e))
        raise err from e


async def create(db, data: UserCreate) -> User:
    await _get_client_or_raise(db, data.client_ids[0])
    return await user_repo.save(db, _build_user(data))


async def get(db, user_id: int) -> User:
    user = await user_repo.get(db, user_id)
    errors = NotFoundError()
    if user is None:
        errors.capture("User")
    errors.raise_if_any()
    return user


async def list_users(db, pagination: PaginatedFilter = None, options: UserFilter = None):
    if pagination is None:
        pagination = PaginatedFilter()
    users = await user_repo.find_all(db, pagination, options)
    total = await user_repo.count(db, options)

    if options and options.id_list:
        found_ids = {u.id for u in users}
        errors = NotFoundError()
        for id_ in options.id_list:
            if id_ not in found_ids:
                errors.capture(f"User {id_}")
        errors.raise_if_any()

    has_more = pagination.offset + len(users) < total
    return PaginatedResponse(items=users, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)


async def update(db, user_id: int, data: UserUpdate) -> User:
    user = await user_repo.get(db, user_id)
    errors = NotFoundError()
    if user is None:
        errors.capture("User")
    errors.raise_if_any()

    if data.client_ids is not None:
        await _get_client_or_raise(db, data.client_ids[0])

    try:
        if data.username is not None:
            user.username = data.username
        if data.password is not None:
            user.password_hash = pwd_context.hash(data.password)
        if data.client_ids is not None:
            user.client_ids = data.client_ids
    except ValueError as e:
        err = DomainValidationError()
        err.capture(str(e))
        raise err from e

    return await user_repo.save(db, user)


async def delete(db, user_id: int):
    user = await user_repo.get(db, user_id)
    errors = NotFoundError()
    if user is None:
        errors.capture("User")
    errors.raise_if_any()
    await user_repo.delete(db, user)


async def login(db, data: LoginRequest) -> LoginResponse:
    user = await user_repo.get_by_username(db, data.username)
    errors = DomainValidationError()
    if user is None or not pwd_context.verify(data.password, user.password_hash):
        errors.capture("Invalid username or password")
    errors.raise_if_any()

    client = await client_repo.get(db, user.client_ids[0])
    return LoginResponse(clients=[LoginClient(client_id=client.id, client_name=client.name)])
