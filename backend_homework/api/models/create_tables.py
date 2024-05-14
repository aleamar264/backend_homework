from utils.database.async_database import sessionmanager


from .user import Base


async def create_tables():
	async with sessionmanager.engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
