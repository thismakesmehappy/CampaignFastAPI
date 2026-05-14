import secrets

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DomainValidationError



_ID_MIN = 10_000_000_000
_ID_MAX = 99_999_999_999
_MAX_RETRIES = 3


def generate_id() -> int:
    return secrets.randbelow(_ID_MAX - _ID_MIN) + _ID_MIN


async def save_with_generated_id(db: AsyncSession, obj) -> object:
    is_insert = obj.id is None
    for attempt in range(_MAX_RETRIES):
        if is_insert:
            obj.id = generate_id()
        try:
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except IntegrityError as e:
            await db.rollback()
            if not is_insert or attempt == _MAX_RETRIES - 1:
                error = DomainValidationError()
                error.capture(str(e))
                raise error from e
        except SQLAlchemyError as e:
            await db.rollback()
            error = DomainValidationError()
            error.capture(str(e))
            raise error from e