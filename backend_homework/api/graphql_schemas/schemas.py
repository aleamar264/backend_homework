from uuid import UUID

import strawberry
from pydantic import BaseModel


@strawberry.type
class PostType:
	id: int
	user_id: UUID
	title: str
	body: str
	private: bool


@strawberry.type
class NotFound:
	message: str


@strawberry.input
class PostInput:
	title: str
	body: str
	private: bool


class PostInputUpdate(BaseModel):
	title: str | None
	body: str | None
	private: bool = False
