from typing import Sequence
from uuid import UUID

from crud.user import user_crud
from fastapi import APIRouter, Depends, Path, Response, status
from fastapi.responses import JSONResponse
from models.user import User as user_model
from pydantic import SecretStr

# from models.user import User
from schemas.user import (
	CreateUser,
	ResponseUser,
	UpdateOtherFields,
	UpdatePassword,
	User,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.async_database import get_db_session
from utils.fastapi.auth.utils import hash_password
from utils.fastapi.exceptions.exceptions_user import InvalidCredentialsError

from .auth import manager

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
	"/",
	response_model=Sequence[ResponseUser] | ResponseUser,
	response_model_exclude={"hashed_password", "created_at", "updated_at"},
	status_code=status.HTTP_200_OK,
)
async def get_users(
	user: User = Depends(manager), db: AsyncSession = Depends(get_db_session)
) -> Sequence[user_model] | user_model:
	if user.role.name == "admin":
		return await user_crud.get_users(db)
	return user


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: CreateUser, db: AsyncSession = Depends(get_db_session)):
	if user.password != user.password2:
		raise ValueError("Passwords do not match")
	password = hash_password(user.password)
	user_ = User(
		**user.model_dump(exclude={"password", "password2"}),
		hashed_password=SecretStr(password),
	)
	await user_crud.create_user(user_, db)


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
	user_id: UUID,
	user: ResponseUser = Depends(manager),
	db: AsyncSession = Depends(get_db_session),
) -> None:
	if user.id == user_id or user.role.name == "admin":
		await user_crud.delete_user(user_id, db)
		return None
	raise InvalidCredentialsError(
		message="You don't have permission to delete this user"
	)


# TODO: PUT/PATCH for the update of password
@router.put("/update/password/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
	user_id: UUID,
	body: UpdatePassword,
	db: AsyncSession = Depends(get_db_session),
	user: ResponseUser = Depends(manager),
):
	print(user_id)
	if user.id == user_id or user.role.name == "admin":
		await user_crud.update_password(user_id, body, db)
		return None
	raise InvalidCredentialsError(
		message="You don't have permission to change the password"
	)


# TODO: PUT/PATCH for the update of the role(Only admin)/other fields
@router.put("/update/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
	body: UpdateOtherFields,
	user_id: UUID = Path(...),
	db: AsyncSession = Depends(get_db_session),
	user: ResponseUser = Depends(manager),
):
	if user.role.name == "admin" or user.id == user_id:
		await user_crud.update_user(user_id, body, db)
		return None
	raise InvalidCredentialsError(
		message="You don't have permission to modify this user"
	)


@router.get("/generate_activation_key/{user_id}", status_code=status.HTTP_200_OK)
async def generate_activation_key(
	user_id: UUID,
	user: ResponseUser = Depends(manager),
	db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
	# TODO: Send this url to mail
	if user.id != user_id:
		raise InvalidCredentialsError(
			message="You don't have permission to generate the key"
		)
	if user.is_active:
		raise InvalidCredentialsError(message="The user is already active")
	activate_user = await user_crud.generate_key(user_id, db)
	return JSONResponse(
		content={
			"url": f"http://localhost/user/activate/{activate_user.id}/{activate_user.activation_key}"
		},
		status_code=status.HTTP_200_OK,
	)


# TODO: Add route for activate the user (is_active)
@router.get("/activate/{user_id}/{key}", status_code=status.HTTP_200_OK)
async def activate_user(
	user_id: UUID,
	key: str,
	db: AsyncSession = Depends(get_db_session),
):
	user = await user_crud.get_user_by_id(user_id, db)
	# TODO: Consult db to know if the key is active or is already use
	if user.is_active:
		raise InvalidCredentialsError(message="You already activate the user")
	if user.activation_key != key:
		raise InvalidCredentialsError(message="Invalid key")
	await user_crud.activate_user(user, db)


# TODO: Create a route to send a mail to activate the user


@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response, user: ResponseUser = Depends(manager)):
	manager.set_cookie(response, None)
	return JSONResponse(content={"message": "Logged out"})
