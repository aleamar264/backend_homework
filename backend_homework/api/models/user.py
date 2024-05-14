import uuid
from datetime import datetime
from typing import Annotated

from schemas.user import Roles
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.database.async_database import Base
from utils.database.general import MixInNameTable

id_annotated = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
str_annotated = Annotated[str, mapped_column(index=True, nullable=False)]


class User(Base, MixInNameTable):
	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		primary_key=True,
		default=uuid.uuid4,
		index=True,
		unique=True,
	)
	email: Mapped[str] = mapped_column(nullable=False, index=True, unique=True)
	username: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
	name: Mapped[str] = mapped_column(nullable=False)
	last_name: Mapped[str] = mapped_column(nullable=True)
	is_active: Mapped[bool] = mapped_column(default=True)
	role: Mapped[Roles] = mapped_column(
		Enum(Roles), nullable=False, default=Roles.user, index=True
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, index=True
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, index=True, onupdate=datetime.now
	)
	hashed_password: Mapped[str] = mapped_column(nullable=False)
	city: Mapped[str] = mapped_column(nullable=True, default=None)
	street: Mapped[str] = mapped_column(nullable=True, default=None)
	country: Mapped[str] = mapped_column(nullable=True, default=None)
	posts: Mapped[list["Post"]] = relationship(back_populates="user", lazy="selectin")


class Post(Base, MixInNameTable):
	id: Mapped[id_annotated]
	user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
	title: Mapped[str_annotated]
	body: Mapped[str_annotated]
	private: Mapped[bool] = mapped_column(default=False)
	user: Mapped["User"] = relationship(back_populates="posts", lazy="selectin")
