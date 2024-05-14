import strawberry

from .controller import CreateMutation, PaginationWindow, Queries
from .schemas import NotFound, PostType

Mutation = CreateMutation()


@strawberry.type
class Query:
	get_all_posts: PaginationWindow[PostType] = strawberry.field(
		resolver=Queries.get_all_post
	)
	get_post: PostType | NotFound = strawberry.field(resolver=Queries.get_post)
