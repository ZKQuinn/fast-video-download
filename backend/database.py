from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 使用 SQLite 异步驱动
DATABASE_URL = "sqlite+aiosqlite:///./fast_download.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# 依赖项：获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
