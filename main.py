from fastapi import FastAPI
from database import engine
from models import Base
from routes import movies

app = FastAPI(
    title="Online Cinema API",
    description="FastAPI-based online cinema",
    version="1.0.0",
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

app.include_router(movies.router)