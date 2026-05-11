from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.client import Client
from app.schema import PaginatedFilter
from app.schema.client import ClientFilter
from app.repositories.base import save_with_generated_id


async def save(db: AsyncSession, client: Client) -> Client:
    return await save_with_generated_id(db, client)


async def get(db: AsyncSession, client_id: int) -> Client | None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


def _apply_filters(query, options: ClientFilter | None):
    if options is None:
        options = ClientFilter()
    query = query.where(Client.name.icontains(options.name_filter))
    if options.id_list:
        query = query.where(Client.id.in_(options.id_list))
    return query


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