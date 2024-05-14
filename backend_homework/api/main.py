from contextlib import asynccontextmanager

import httpx
import strawberry
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from graphql_schemas.controller import CreateMutation, get_context
from graphql_schemas.core import Query
from routers.auth import auth_router
from routers.user import router as user
from strawberry.fastapi import GraphQLRouter
from utils.database.async_database import sessionmanager
from utils.fastapi.exceptions import exceptions_user, general


@asynccontextmanager
async def lifespan(_app: FastAPI):
	"""
	    Function that handles startup and shutdown events.
	To understand more, read https://fastapi.tiangolo.com/advanced/events/"""
	yield
	if sessionmanager.engine is not None:
		await sessionmanager.async_close()


app = FastAPI(
	version="0.1.0",
	title="Pokemon blog",
	lifespan=lifespan,
)

allow_origins = ["*"]
allow_methods = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=allow_origins,
	allow_credentials=True,
	allow_methods=allow_methods,
	allow_headers=["*"],
)

schema = strawberry.Schema(query=Query, mutation=CreateMutation)
graphql_app = GraphQLRouter(
	schema,
	context_getter=get_context,
)

app.include_router(user)
app.include_router(auth_router)
app.include_router(graphql_app, prefix="/graphql")

app.add_exception_handler(
	exc_class_or_status_code=exceptions_user.EntityDoesNotExistError,
	handler=exceptions_user.create_exception_handler(
		status.HTTP_404_NOT_FOUND, "Entity does not exist."
	),
)

app.add_exception_handler(
	exc_class_or_status_code=general.ServiceError,
	handler=exceptions_user.create_exception_handler(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		initial_detail="Internal server error.",
	),
)

app.add_exception_handler(
	exc_class_or_status_code=exceptions_user.EntityAlreadyExistsError,
	handler=exceptions_user.create_exception_handler(
		status_code=status.HTTP_400_BAD_REQUEST,
		initial_detail="User already already exists.",
	),
)

app.add_exception_handler(
	exc_class_or_status_code=exceptions_user.EntityDoesNotExistError,
	handler=exceptions_user.create_exception_handler(
		status_code=status.HTTP_404_NOT_FOUND, initial_detail="User does not exist."
	),
)


app.add_exception_handler(
	exc_class_or_status_code=exceptions_user.LoginError,
	handler=exceptions_user.create_exception_handler(
		status_code=status.HTTP_401_UNAUTHORIZED, initial_detail="Invalid credentials."
	),
)

app.add_exception_handler(
	exc_class_or_status_code=exceptions_user.InvalidCredentialsError,
	handler=exceptions_user.create_exception_handler(
		status_code=status.HTTP_401_UNAUTHORIZED, initial_detail="Invalid credentials."
	),
)


@app.get("/")
async def root():
	return {"message": "Welcome to the Pokemon blog!"}


@app.get("/get_random_number")
async def get_random_number() -> JSONResponse:
	async with httpx.AsyncClient() as client:
		response = await client.get(
			"http://www.randomnumberapi.com/api/v1.0/randomnumber"
		)
		data = response.json()
	return JSONResponse(
		content={"your random number is": data[0]}, status_code=status.HTTP_200_OK
	)
