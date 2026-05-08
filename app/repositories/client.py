from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.client import Client
from app.schema import PaginatedFilter
from app.exceptions import DomainValidationError
from app.schema.client import ClientFilter


async def save(db: AsyncSession, client: Client) -> Client:
    try:
        db.add(client)
        await db.commit()
        await db.refresh(client)
        return client
    except SQLAlchemyError as e:
        await db.rollback()
        error = DomainValidationError()
        error.capture(str(e))
        raise error from e


async def get(db: AsyncSession, client_id: int) -> Client | None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


def _apply_filters(query, options: ClientFilter | None):
    if options is None:
        options = ClientFilter()
    return query.where(Client.name.icontains(options.name_filter))


async def find_all(db: AsyncSession, data: PaginatedFilter = None, options: ClientFilter = None) -> list[Client]:
    if data is None:
        data = PaginatedFilter()
    query = _apply_filters(select(Client), options).offset(data.offset).limit(data.limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count(db: AsyncSession, options: ClientFilter = None) -> int:
    query = _apply_filters(select(func.count()).select_from(Client), options)
    result = await db.execute(query)
    return int(result.scalar() or 0)


async def delete(db: AsyncSession, client: Client) -> None:
    await db.delete(client)
    await db.commit()