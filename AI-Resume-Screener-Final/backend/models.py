from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(200), default="")
    department = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, default="")

    skills = Column(Text, default="[]")
    ats_score = Column(Float, default=0)
    similarity_score = Column(Float, default=0)
    skills_match_score = Column(Float, default=0)
    completeness_score = Column(Float, default=0)

    job_description = Column(Text, default="")
    matched_skills = Column(Text, default="[]")
    missing_skills = Column(Text, default="[]")
    suggestions = Column(Text, default="[]")

    education = Column(Text, default="[]")
    experience = Column(Text, default="[]")

    candidate_name = Column(String(250), default="Unknown candidate")
    email = Column(String(320), default="")
    phone = Column(String(80), default="")
    job_title = Column(String(200), default="")
    status = Column(String(40), default="Review")
    recruiter_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
