from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.client import Client
from app.schema import PaginatedFilter
from app.schema.client import ClientFilter
from app.repositories.base import save_with_generated_id, apply_sort


async def save(db: AsyncSession, client: Client) -> Client:
    return await save_with_generated_id(db, client)


async def get(db: AsyncSession, client_id: int) -> Client | None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


def _apply_filters(query, options: ClientFilter | None, sortable: bool = False):
    sort_by_options = {
        "id": Client.id,
        "name": Client.name,
        "email": Client.email,
        "notes": Client.notes,
        "is_active": Client.is_active,
        "created_at": Client.created_at
    }

    if options is None:
        options = ClientFilter()
    query = query.where(Client.name.icontains(options.name_filter))
    if options.id_list:
        query = query.where(Client.id.in_(options.id_list))
    
    return apply_sort(
        query,
        options.sort_by_list,
        sort_by_options,
        options.desc,
        sortable
    )


async def find_all(db: AsyncSession, data: PaginatedFilter = None, options: ClientFilter = None) -> list[Client]:
    if data is None:
        data = PaginatedFilter()
    query = _apply_filters(select(Client), options, sortable=True).offset(data.offset).limit(data.limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count(db: AsyncSession, options: ClientFilter = None) -> int:
    query = _apply_filters(select(func.count()).select_from(Client), options)
    result = await db.execute(query)
    return int(result.scalar() or 0)


async def delete(db: AsyncSession, client: Client) -> None:
    await db.delete(client)
    await db.commit()

async def find_ids(db: AsyncSession, ids: list[int]) -> list[int]:
    query = select(Client.id).where(Client.id.in_(ids))
    result = await db.execute(query)
    return list(result.scalars().all())