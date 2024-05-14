from asyncio import run
from uuid import UUID

import httpx
from models.user import Post, User
from schemas.user import CreateUser
from sqlalchemy import select
from utils.database.async_database import sessionmanager
from utils.fastapi.auth.utils import hash_password


async def populate_db_users() -> UUID:
	async with sessionmanager.async_session() as session:
		stmt = select(User).where(User.username == "admin")
		result = await session.execute(stmt)
		if user := result.scalar_one_or_none():
			id_ = user.id
			return id_
		user_ = CreateUser(
			**{
				"email": "jhondoe@example.com",
				"is_active": True,
				"last_name": "Doe",
				"name": "Jhon",
				"password": "TalkAboutPokemon!",
				"password2": "TalkAboutPokemon!",
				"role": "admin",
				"username": "admin",
			}
		)
		new_admin = User(
			**user_.model_dump(exclude={"password", "password2"}),
			hashed_password=hash_password("TalkAboutPokemon!"),
		)
		session.add(new_admin)
		await session.commit()
		return new_admin.id


async def populate_db_posts(user_id: UUID):
	async with httpx.AsyncClient() as client:
		response = await client.post(
			"http://api:8000/graphql",
			json={
				"query": """query MyQuery {
						getAllPosts(limit: 5, offset: 0, private: false) {
							items {
							body
							}
							totalItemsCount
						}
						}"""
			},
		)

	data = response.json()
	if data["data"]["getAllPosts"]["totalItemsCount"] == 0:
		async with sessionmanager.async_session() as session:
			title: list[str] = [
				"Pokemon Card Game May 2024 Merchandise Revealed",
				"Ultra PRO Pokémon - Gallery Series: Morning Meadow Product Line Announced",
				"Pokemon Go Fest Madrid 2024",
				"""The Ad Council and Feeding America Launch AR Experience Geared Towards Ending Hunger""",
				"""Pokémon Of The Day""",
				"""Videos: Watch the 2024 Pokémon UNITE Championship Series Finales Regionales de Latinoamérica - Norte and more""",
			]
			body: list[str] = [
				"""
					The Pokemon Card Game Scarlet & Violet Merchandise line-up for May 2024 has been revealed.
					All of these products release on May 17, 2024.
					These products are Pokemon Center or Pokemon Store Japan exclusive.""",
				"""Ultra PRO has revealed a new Pokémon collection. And it's called the Gallery Series: Morning Meadow this time. The exact release date for this collection. as with most Ultra Pro Pokémon collections, is currently unknown. We will update this article if we see a placeholder date.

						It features Skiddo, Meowscarada, Deerling & Hoppip.
						No MSRP mentioned, but we think it's the same as the previous Gallery Series.""",
				"""Trainers, get ready to head to Madrid, Spain for the European edition of Pokémon GO Fest 2024! You'll 
				be able to enjoy exploring the vibrant and rich culture of southern Europe’s biggest city. Adventure awaits among the parks and boulevards of Spain’s capital city on the second weekend of Pokémon GO Fest 2024""",
				"""Starting today, the public can access the immersive web-based augmented reality (WebAR) experience, exploring true stories and statistics about the impact of food on people’s lives, and how they can join the movement to end hunger. Feeding America® and the Ad Council, in partnership with Niantic 8th Wall, 
				Sawhorse Productions, and Flowcode, today launched this new augmented reality (AR) experience designed to raise awareness about hunger in the United States.""",
				"""Golett is a bipedal Pokémon said to have been constructed from clay in the ancient past to protect an ancient and mysterious civilization of people and Pokémon.
				  Its body is primarily covered by two different shades of blue. Its head features two bewitching, yellow eyes and a stub-like cyan-colored crest on top. Tw
				o pairs of crisscrossing brown bands extend around its spherical body meeting at a blue square with a yellow swirl in the center.
				  Two large stone-like blocks act as its feet and two more such blocks adorn its “forearms”; each arm ends in a dark blue-colored, crude three-fingered hand."""
				"""¡Bienvenidos a las Finales Regionales de Latinoamérica - Norte de la Serie de Campeonatos Pokémon UNITE! Los 16 mejores equipos de la región comenzaron hoy luchando en 4 grupos de 4, y los 2 mejores equipos de cada grupo avanzaron a un cuadro de doble eliminación.

					¡Ahora, esos 8 mejores equipos competirán hasta que uno se convierta en el Campeón Regional de Latinoamérica - Norte que clasificará para el Campeonato Mundial en Honolulú!

					Además, el mejor equipo de la región determinado por Championship Points obtenidos esta temporada, además de los campeones regionales, también se clasificará para el Campeonato Mundial.

					¡Es hora de que los equipos lo den todo en las Finales Regionales de Latinoamérica - Norte!""",
			]

			posts = [
				Post(user_id=user_id, private=False, title=t, body=b)
				for t, b in zip(title, body)
			]

			session.add_all(posts)
			await session.commit()


async def main():
	user_id = await populate_db_users()
	print(user_id)
	await populate_db_posts(user_id)


if __name__ == "__main__":
	run(main())
