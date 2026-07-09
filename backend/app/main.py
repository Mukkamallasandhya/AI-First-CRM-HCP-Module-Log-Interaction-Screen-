from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import interactions, hcp, chat

# Creates tables on startup if they don't exist yet (fine for a dev/demo setup;
# use Alembic migrations for a real production rollout).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM - HCP Interaction Module", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(hcp.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
