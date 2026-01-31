import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to SQLite for local development, Cloud SQL (Postgres) for production
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sue_local.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=True, # Set to False in production
)

# Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
