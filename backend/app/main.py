from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

# Import all models so SQLAlchemy registers them before create_all
import app.models  # noqa: F401

from app.routers import auth, circles, memberships, availability, viability, day_overrides, day_notes
from app.services.notifications import start_scheduler, shutdown_scheduler


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="MeepleTime API",
    description="Backend API for the MeepleTime meeting availability application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(circles.router)
app.include_router(memberships.router)
app.include_router(availability.router)
app.include_router(viability.router)
app.include_router(day_overrides.router)
app.include_router(day_notes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
