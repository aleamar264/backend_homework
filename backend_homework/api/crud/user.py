from typing import Sequence, override
from uuid import UUID, uuid4

from models.user import User
from schemas.user import ActivateUser, UpdateOtherFields, UpdatePassword
from schemas.user import User as user_create
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.crud.general import GeneralCrudAsync
from utils.fastapi.auth.utils import hash_password
from utils.fastapi.exceptions.exceptions_user import (
	EntityAlreadyExistsError,
	EntityDoesNotExistError,
)


class UserCrudAsync(GeneralCrudAsync[User]):
	def __init__(self, model=User) -> None:
		super().__init__(model)

	@override
	async def get_users(self, db: AsyncSession) -> Sequence[User]:
		stmt = select(self.model)
		result = await db.execute(stmt)
		return result.scalars().all()

	@override
	async def get_user_by_email(
		self, email: str, db: AsyncSession, new_user: bool = False
	) -> User:
		stmt = select(self.model).where(self.model.email == email)
		result = await db.execute(statement=stmt)
		if not (user := result.scalar_one_or_none()) and not new_user:
			raise EntityDoesNotExistError(message="User don't exist")
		return user

	@override
	async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
		stmt = select(self.model).where(self.model.id == user_id)
		result = await db.execute(statement=stmt)
		if not (user := result.scalar_one_or_none()):
			raise EntityDoesNotExistError(message="User don't exist")
		return user

	@override
	async def get_user_by_username(self, username: str, db: AsyncSession) -> User:
		stmt = select(self.model).where(self.model.username == username)
		result = await db.execute(statement=stmt)
		if (user := result.scalar_one_or_none()) is None:
			raise EntityDoesNotExistError(message="User don't exist")
		return user

	@override
	async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
		user = await self.get_user_by_id(user_id, db)
		await db.delete(user)
		await db.commit()

	@override
	async def create_user(self, user: user_create, db: AsyncSession) -> User:
		user_ = await self.get_user_by_email(user.email, db, new_user=True)
		if user_:
			raise EntityAlreadyExistsError(
				message=f"User with email {user.email} alerady is registered"
			)
		user_ = user.model_dump()
		user_["hashed_password"] = user_["hashed_password"].get_secret_value()
		user_ = self.model(**user_)

		db.add(user_)
		await db.commit()
		await db.refresh(user_)
		return user_

	@override
	async def update_user(
		self, user_id: UUID, user: UpdateOtherFields, db: AsyncSession
	) -> User:
		user_ = await self.get_user_by_id(user_id, db)
		if not user_:
			raise EntityDoesNotExistError(message="User don't exist")
		for attr, value in user.model_dump().items():
			setattr(user_, attr, value)
		await db.commit()
		await db.refresh(user_)
		return user_

	@override
	async def update_password(
		self, user_id: UUID, user: UpdatePassword, db: AsyncSession
	):
		user_ = user.model_dump()
		password = hash_password(user_["new_password"].get_secret_value())
		user_to_update = await self.get_user_by_id(user_id, db)
		setattr(user_to_update, "hashed_password", password)
		await db.commit()
		await db.refresh(user_to_update)
		return user_to_update

	@override
	async def activate_user(self, user: User, db: AsyncSession):
		setattr(user, "is_active", True)
		await db.commit()
		await db.refresh(user)
		return None

	async def generate_key(self, user_id: UUID, db: AsyncSession) -> ActivateUser:
		user = await self.get_user_by_id(user_id, db)
		setattr(user, "activation_key", uuid4().hex.upper())
		await db.commit()
		await db.refresh(user)
		return ActivateUser(
			is_active=user.is_active, id=user.id, activation_key=user.activation_key
		)


user_crud = UserCrudAsync()
