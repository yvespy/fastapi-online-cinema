from fastapi import FastAPI

app = FastAPI(
    title="Online Cinema API",
    description="FastAPI-based online cinema",
    version="1.0.0",
)


@app.get("/")
async def read_root():
    return {"message": "Hello World"}
