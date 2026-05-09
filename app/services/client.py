from app.repositories import client as client_repo
from app.exceptions import NotFoundError, DomainValidationError
from app.models import Client
from app.schema import PaginatedFilter, PaginatedResponse
from app.schema.client import ClientCreate, ClientUpdate, ClientFilter


def _build_client(data) -> Client:
    try:
        return Client(name=data.name, api_key=data.api_key, email=data.email, notes=data.notes, is_active=data.is_active)
    except ValueError as e:
        err = DomainValidationError()
        err.capture(str(e))
        raise err from e


async def create(db, data: ClientCreate) -> Client:
    return await client_repo.save(db, _build_client(data))


async def get(db, client_id: int) -> Client:
    client = await client_repo.get(db, client_id)
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()
    return client


async def list_clients(db, pagination: PaginatedFilter = None, options: ClientFilter = None):
    if pagination is None:
        pagination = PaginatedFilter()
    clients = await client_repo.find_all(db, pagination, options)
    total = await client_repo.count(db, options)
    has_more = pagination.offset + len(clients) < total
    return PaginatedResponse(items=clients, has_more=has_more, total=total, offset=pagination.offset, limit=pagination.limit)


async def update(db, client_id: int, data: ClientUpdate) -> Client:
    client = await client_repo.get(db, client_id)
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()

    try:
        if data.name is not None:
            client.name = data.name
        if data.email is not None:
            client.email = data.email
        if data.notes is not None:
            client.notes = data.notes
        if data.is_active is not None:
            client.is_active = data.is_active
    except ValueError as e:
        err = DomainValidationError()
        err.capture(str(e))
        raise err from e

    return await client_repo.save(db, client)


async def delete(db, client_id: int):
    client = await client_repo.get(db, client_id)
    errors = NotFoundError()
    if client is None:
        errors.capture("Client")
    errors.raise_if_any()
    await client_repo.delete(db, client)