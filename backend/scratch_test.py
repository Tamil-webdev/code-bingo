import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models.tournament import Tournament, TournamentStatus

async def test():
    async with async_session_maker() as db:
        res = await db.execute(select(Tournament).where(Tournament.status == "active"))
        tournaments = res.scalars().all()
        for t in tournaments:
            print(f"Tournament: {t.id} - {t.name} (Status: {t.status})")

if __name__ == "__main__":
    asyncio.run(test())
