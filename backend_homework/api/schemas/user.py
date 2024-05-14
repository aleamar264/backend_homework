import re
from datetime import UTC, datetime
from enum import Enum
from typing import Self

from pydantic import UUID4, BaseModel, EmailStr, Field, SecretStr, model_validator


class Roles(str, Enum):
	admin = "admin"
	user = "user"


def datetime_now():
	return datetime.now(UTC)


class UserBase(BaseModel):
	email: EmailStr
	username: str = Field(max_length=25)
	name: str
	last_name: str | None = None
	is_active: bool = True
	role: Roles = Field(default=Roles.user)
	created_at: datetime = Field(default_factory=datetime_now)
	updated_at: datetime = Field(default_factory=datetime_now)
	city: str | None = None
	street: str | None = None
	country: str | None = None

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"email": "jhondoe@example.com",
					"username": "jhondoe",
					"name": "Jhon",
					"last_name": "Doe",
					"is_active": False,
					"role": Roles.user.name,
					"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"city": None,
					"street": None,
					"country": None,
				}
			]
		}
	}


class User(UserBase):
	hashed_password: SecretStr | str


class ResponseUser(UserBase):
	id: UUID4


class UpdateOtherFields(BaseModel):
	city: str | None = None
	street: str | None = None
	country: str | None = None
	state: str | None = None
	zip_code: int | None = None
	phone: str | None = None


class CreateUser(UserBase):
	password: str = Field(min_length=8)
	password2: str = Field(min_length=8)

	@model_validator(mode="after")
	def check_passwords_match(self) -> Self:
		pw1 = self.password
		pw2 = self.password2
		if pw1 is not None and pw2 is not None and pw1 != pw2:
			raise ValueError("passwords do not match")
		if len(pw1) < 10:
			raise ValueError("password must be at least 10 characters")
		reg = r"(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#?\]])[A-Za-z!@#?\]]{10,}"
		pat = re.compile(reg)
		mat = re.search(pat, pw1)
		if not mat:
			raise ValueError(
				"password must contain at least one uppercase letter, one lowercase letter, or one of the following special character !@#?]"
			)
		return self

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"email": "jhondoe@example.com",
					"username": "jhondoe",
					"name": "Jhon",
					"last_name": "Doe",
					"is_active": False,
					"role": Roles.user.name,
					"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"city": None,
					"street": None,
					"country": None,
					"state": None,
					"zip_code": None,
					"phone": None,
					"password": "12345678",
					"password2": "12345678",
				}
			]
		}
	}


class UpdatePassword(BaseModel):
	old_password: SecretStr
	new_password: SecretStr = Field(min_length=8)

	@model_validator(mode="after")
	def check_passwords_match(self) -> Self:
		pw1 = self.old_password
		pw2 = self.new_password
		if pw1 is not None and pw2 is not None and pw1 != pw2:
			raise ValueError("passwords do not match")
		return self

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"email": "jhondoe@example.com",
					"username": "jhondoe",
					"name": "Jhon",
					"last_name": "Doe",
					"is_active": False,
					"role": Roles.user.name,
					"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"city": None,
					"street": None,
					"country": None,
					"state": None,
					"zip_code": None,
					"phone": None,
					"old_password": "12345678",
					"new_password": "12345678",
				}
			]
		}
	}


class ActivateUser(BaseModel):
	is_active: bool
	id: UUID4
	activation_key: str
