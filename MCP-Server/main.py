from fastapi import FastAPI
from contextlib import asynccontextmanager
from mcp_server import mcp as mcp_server

mcp_app = mcp_server.http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(lifespan=lifespan)


app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4
    )