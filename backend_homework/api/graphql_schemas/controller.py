import uuid
from functools import cached_property
from typing import Generic, TypeVar

import strawberry
import strawberry.exceptions
from jwt import decode
from models.user import Post, User
from sqlalchemy import select
from strawberry.fastapi import BaseContext
from utils.database.async_database import sessionmanager
from utils.fastapi.auth.secret_key import secret_key
from utils.fastapi.exceptions import exceptions_user

from .schemas import NotFound, PostInput, PostInputUpdate, PostType


class Context(BaseContext):
	@cached_property
	def user(self) -> User | None:
		if not self.request:
			return None

		if (auth := self.request.cookies.get("auth", None)) is None:
			raise exceptions_user.LoginError("No auth cookie")
		auth_decode: dict[str, str] = decode(
			auth, secret_key.secret_key, algorithms=["HS256"]
		)
		user_id = auth_decode["sub"].split("_*")[-1]
		return uuid.UUID(user_id)


async def get_context() -> Context:
	return Context()


@strawberry.type
class CreateMutation:
	@strawberry.mutation
	async def add_post(
		self, post_data: PostInput, info: strawberry.Info[Context]
	) -> PostType | NotFound:
		async with sessionmanager.async_session() as db:
			stmt = select(User).where(User.id == info.context.user)
			result = await db.execute(stmt)
		if (user := result.scalar_one_or_none()) is None:
			return NotFound(message="User don't found")
		async with sessionmanager.async_session() as db:
			post: Post = Post(**post_data.__dict__, user_id=info.context.user)
			db.add(post)
			await db.commit()
			await db.refresh(post)
		return PostType(
			body=post.body,
			id=post.id,
			user_id=post.user_id,
			title=post.title,
			private=post.private,
		)

	@strawberry.mutation
	async def update_post(
		self,
		id: int,
		private: bool,
		info: strawberry.Info[Context],
		title: str | None = None,
		body: str | None = None,
	) -> PostType | NotFound:
		async with sessionmanager.async_session() as db:
			stmt = select(User).where(User.id == info.context.user)
			user = await db.execute(stmt)
			user = user.scalar_one_or_none()
		if not user:
			return NotFound(message="User don't found")
		async with sessionmanager.async_session() as db:
			post_data = PostInputUpdate(
				private=private,
				title=title,
				body=body,
			)
			stmt = select(Post).where(Post.id == id, Post.user_id == info.context.user)
			post = await db.execute(stmt)
			post = post.scalar_one_or_none()
			if not post:
				return NotFound(message="Post don't found or invalid account")
			post_data_ = post_data.model_dump(exclude_unset=True)
			for key, value in post_data_.items():
				if value is not None:
					setattr(post, key, value)
			await db.commit()
			# await db.refresh(post_data)
		return await Queries().get_post(
			info=info,
			post_id=id,
			private=private,
		)


Item = TypeVar("Item")


@strawberry.type
class PaginationWindow(Generic[Item]):
	items: list[Item] = strawberry.field(
		description="The list of items in this pagination window."
	)

	total_items_count: int = strawberry.field(
		description="Total number of items in the filtered dataset."
	)


class Queries:
	async def get_all_post(
		self,
		info: strawberry.Info[Context],
		limit: int = 10,
		offset: int = 0,
		private: bool = True,
		order_by: str = "asc",
	) -> PaginationWindow[PostType]:
		return await get_pagination_window_post(
			info=info,
			ItemType=Post,
			limit=limit,
			offset=offset,
			order_by=order_by,
			private=private,
		)

	async def get_post(
		self,
		info: strawberry.Info[Context],
		post_id: int,
		private: bool = True,
	) -> PostType | NotFound:
		async with sessionmanager.async_session() as session:
			if private:
				stmt = select(Post).filter(
					Post.id == post_id,
					Post.user_id == info.context.user,
					Post.private == private,
				)
			else:
				stmt = select(Post).filter(
					Post.id == post_id,
					Post.private == private,
				)
			result = await session.execute(stmt)
			if (post := result.scalar_one_or_none()) is None:
				return NotFound(message="Post don't found")
			return PostType(
				body=post.body,
				id=post.id,
				user_id=post.user_id,
				title=post.title,
				private=post.private,
			)


async def get_pagination_window_post(
	info: strawberry.Info[Context],
	ItemType: type,
	order_by: str,
	limit: int,
	offset: int = 0,
	private: bool = True,
) -> PaginationWindow[PostType]:
	"""
	Get one pagination window on the given dataset for the given limit
	and offset, ordered by the given attribute and filtered using the
	given filters
	"""

	if limit <= 0 or limit > 100:
		raise Exception(f"limit ({limit}) must be between 0-100")

	async with sessionmanager.async_session() as db:
		if private:
			stmt = (
				select(ItemType)
				.order_by(
					ItemType.id.asc() if order_by == "asc" else ItemType.id.desc()
				)
				.filter(ItemType.user_id == info.context.user)
				.offset(offset)
				.limit(limit)
			)
		else:
			stmt = (
				select(ItemType)
				.order_by(
					ItemType.id.asc() if order_by == "asc" else ItemType.id.desc()
				)
				.filter(ItemType.private == private)
				.offset(offset)
				.limit(limit)
			)

		sorted_items = await db.execute(stmt)
		# sorted_items = await db.execute(stmt)
		sorted_items = sorted_items.scalars().all()
		items: list[PostType] = [
			PostType(
				body=item.body,
				id=item.id,
				user_id=item.user_id,
				title=item.title,
				private=item.private,
			)
			for item in sorted_items
		]

		total_items_count = len(items)

		return PaginationWindow(items=items, total_items_count=total_items_count)
