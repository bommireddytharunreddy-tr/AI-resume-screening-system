from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine, migrate_existing_database
from backend.models import Job, Resume  # noqa: F401
from backend.routes.resume import router

Base.metadata.create_all(bind=engine)
migrate_existing_database()

app = FastAPI(
    title="AI Resume Screening Platform",
    description="Recruiter-focused resume screening and job matching API.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "service": "AI Resume Screening Platform",
        "status": "online",
        "version": "2.0.0",
    }
