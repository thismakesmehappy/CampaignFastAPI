from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.schema import PaginatedFilter
from app.schema.user import UserFilter
from app.repositories.base import save_with_generated_id, apply_sort


async def save(db: AsyncSession, user: User) -> User:
    return await save_with_generated_id(db, user)


async def get(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


def _apply_filters(query, options: UserFilter | None, sortable: bool = False):
    sort_by_options = {
        "id": User.id,
        "username": User.username,
        "created_at": User.created_at,
    }

    if options is None:
        options = UserFilter()
    query = query.where(User.username.icontains(options.username_filter))
    if options.id_list:
        query = query.where(User.id.in_(options.id_list))

    return apply_sort(
        query,
        options.sort_by_list,
        sort_by_options,
        options.desc,
        sortable
    )


async def find_all(db: AsyncSession, data: PaginatedFilter = None, options: UserFilter = None) -> list[User]:
    if data is None:
        data = PaginatedFilter()
    query = _apply_filters(select(User), options, sortable=True).offset(data.offset).limit(data.limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count(db: AsyncSession, options: UserFilter = None) -> int:
    query = _apply_filters(select(func.count()).select_from(User), options)
    result = await db.execute(query)
    return int(result.scalar() or 0)


async def delete(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
