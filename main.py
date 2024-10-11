from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from db.create_database import create_tables
from db.database import SessionLocal
from routers import auth


@asynccontextmanager
async def lifespan(app):
    create_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="To-Do List Application API",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "To-Do List Application",
    },
    servers=[{"url": "http://localhost:8000", "description": "Local server"}],
)


@app.get("/")
async def main_route():
    return {"message": "Hey, It is me Goku"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response
