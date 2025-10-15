# See fail on mõeldud korduvkasutatava loogika jaoks, mida saab kasutada erinevates API lõpp-punktides.

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

# TULEVIKU NÄIDE: Andmebaasiühenduse haldamine
# See oleks funktsioon, mis loob andmebaasiühenduse iga päringu jaoks ja sulgeb selle pärast päringu lõppu.
#
# from .database import SessionLocal
#
# async def get_db_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()