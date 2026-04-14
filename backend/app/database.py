from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


def get_database_url():
    """DATABASE_URL을 async 드라이버에 맞게 변환"""
    url = settings.DATABASE_URL
    # Render 등에서 제공하는 postgres:// → postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


db_url = get_database_url()

engine = create_async_engine(
    db_url,
    echo=settings.ENVIRONMENT == "development",
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # 기존 테이블에 신규 컬럼이 없으면 추가 (간이 마이그레이션)
        # Postgres용. 컬럼이 이미 있으면 조용히 실패.
        migrations = [
            "ALTER TABLE ai_accounts ADD COLUMN IF NOT EXISTS avatar_data BYTEA",
            "ALTER TABLE ai_accounts ADD COLUMN IF NOT EXISTS avatar_mime VARCHAR",
        ]
        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                # SQLite 등 다른 DB에서는 IF NOT EXISTS 문법이 다를 수 있음
                print(f"Migration skipped: {stmt} - {e}")

    # 기존 /uploads/ 경로로 깨진 아바타들을 DB 기반 랜덤 아바타로 복구
    from app.models import AIAccount
    from sqlalchemy import select, update
    from app.utils.avatar import generate_random_avatar
    import hashlib

    async with async_session() as session:
        result = await session.execute(
            select(AIAccount).where(
                (AIAccount.avatar_data.is_(None))
                | (AIAccount.avatar_url.like("/uploads/%"))
            )
        )
        broken_ais = result.scalars().all()
        for ai in broken_ais:
            try:
                avatar_bytes = generate_random_avatar(ai.name)
                version = hashlib.md5(avatar_bytes).hexdigest()[:8]
                ai.avatar_data = avatar_bytes
                ai.avatar_mime = "image/png"
                ai.avatar_url = f"/api/ai/{ai.id}/avatar?v={version}"
            except Exception as e:
                print(f"Avatar regen failed for AI {ai.id}: {e}")
        if broken_ais:
            await session.commit()
            print(f"Regenerated avatars for {len(broken_ais)} AI(s)")
