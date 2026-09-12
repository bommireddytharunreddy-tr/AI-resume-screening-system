import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.ai.parser import ResumeParser
from backend.ai.profile_extractor import ProfileExtractor
from backend.ai.similarity import ResumeSimilarity
from backend.ai.skill_extractor import SkillExtractor
from backend.database import get_db
from backend.models import Job, Resume

router = APIRouter()
UPLOAD_FOLDER = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
VALID_STATUSES = {"Review", "Shortlisted", "On Hold", "Rejected"}


def calculate_skill_match(resume_skills, required_skills):
    required = {s.lower() for s in required_skills}
    resume = {s.lower() for s in resume_skills}
    if not required:
        return 100.0
    return round(len(required & resume) / len(required) * 100, 2)


def calculate_completeness(resume_text, skills, education, experience):
    checks = [
        len((resume_text or "").strip()) >= 100,
        bool(skills),
        bool(education),
        bool(experience),
    ]
    return round(sum(checks) / len(checks) * 100, 2)


def calculate_fit_score(skill_score, similarity_score, completeness_score):
    # Skill alignment is intentionally weighted highest because it is explicit
    # and easier for a recruiter to audit than a black-box score.
    return round(
        min(100.0, skill_score * 0.50 + similarity_score * 0.35 + completeness_score * 0.15),
        2,
    )


def recommendation(score):
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Shortlist"
    if score >= 55:
        return "Review"
    return "Low Match"


def safe_json(value, default=None):
    if default is None:
        default = []
    try:
        return json.loads(value) if value else default
    except (TypeError, json.JSONDecodeError):
        return default


def serialize_record(record, include_text=False):
    data = {
        "id": record.id,
        "filename": record.filename,
        "candidate_name": record.candidate_name or "Unknown candidate",
        "email": record.email or "",
        "phone": record.phone or "",
        "job_title": record.job_title or "",
        "status": record.status or "Review",
        "recruiter_notes": record.recruiter_notes or "",
        "created_at": record.created_at.isoformat() if record.created_at else "",
        "analysis": {
            "fit_score": round(record.ats_score or 0, 2),
            "semantic_similarity_score": round(record.similarity_score or 0, 2),
            "skills_match_score": round(record.skills_match_score or 0, 2),
            "resume_completeness_score": round(record.completeness_score or 0, 2),
            "recommendation": recommendation(record.ats_score or 0),
        },
        "skills": {
            "resume_skills": safe_json(record.skills),
            "matched_skills": safe_json(record.matched_skills),
            "missing_skills": safe_json(record.missing_skills),
        },
        "profile": {
            "education": safe_json(record.education),
            "experience": safe_json(record.experience),
        },
        "suggestions": safe_json(record.suggestions),
    }
    if include_text:
        data["resume_text"] = record.extracted_text or ""
        data["job_description"] = record.job_description or ""
    return data


@router.get("/status")
def status():
    return {"status": "online", "service": "AI Resume Screening Platform"}


@router.get("/test")
def test_route():
    return {"message": "Resume router is working"}


@router.post("/jobs")
def create_job(
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(""),
    department: str = Form(""),
    db: Session = Depends(get_db),
):
    title = title.strip()
    description = description.strip()
    if not title or not description:
        raise HTTPException(status_code=400, detail="Job title and description are required.")

    job = Job(
        title=title,
        description=description,
        location=location.strip(),
        department=department.strip(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "department": job.department,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location or "",
            "department": job.department or "",
            "created_at": job.created_at.isoformat(),
        }
        for job in jobs
    ]


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    db.delete(job)
    db.commit()
    return {"success": True}


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form(""),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No resume file provided.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported.")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    unique_name = f"{uuid.uuid4()}{extension}"
    file_path = UPLOAD_FOLDER / unique_name

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        resume_text = ResumeParser.extract_text(str(file_path)).strip()
        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found. The PDF may be scanned/image-only.",
            )

        resume_skills = SkillExtractor.extract(resume_text)
        required_skills = SkillExtractor.extract(job_description)

        resume_set = {skill.lower() for skill in resume_skills}
        required_set = {skill.lower() for skill in required_skills}
        matched = sorted(resume_set & required_set)
        missing = sorted(required_set - resume_set)

        profile = ProfileExtractor.extract_profile(resume_text)
        skill_score = calculate_skill_match(resume_skills, required_skills)
        similarity_score = ResumeSimilarity.calculate(resume_text, job_description)
        completeness_score = calculate_completeness(
            resume_text,
            resume_skills,
            profile["education"],
            profile["experience"],
        )
        fit_score = calculate_fit_score(
            skill_score,
            similarity_score,
            completeness_score,
        )

        suggestions = []
        if missing:
            suggestions.append(
                "Verify whether the candidate has equivalent experience for the missing requirements: "
                + ", ".join(missing[:8])
                + "."
            )
        if not profile["education"]:
            suggestions.append("Education details were not clearly detected; verify manually.")
        if not profile["experience"]:
            suggestions.append("Experience details were not clearly detected; verify manually.")
        if not suggestions:
            suggestions.append("No major extraction gaps were detected. Continue with human review.")

        record = Resume(
            filename=file.filename,
            extracted_text=resume_text,
            skills=json.dumps(resume_skills),
            ats_score=fit_score,
            similarity_score=similarity_score,
            skills_match_score=skill_score,
            completeness_score=completeness_score,
            job_description=job_description.strip(),
            matched_skills=json.dumps(matched),
            missing_skills=json.dumps(missing),
            suggestions=json.dumps(suggestions),
            education=json.dumps(profile["education"]),
            experience=json.dumps(profile["experience"]),
            candidate_name=profile["name"],
            email=profile["email"],
            phone=profile["phone"],
            job_title=job_title.strip(),
            status="Shortlisted" if fit_score >= 85 else "Review",
            recruiter_notes="",
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "success": True,
            **serialize_record(record, include_text=True),
        }

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Screening failed: {exc}") from exc
    finally:
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


@router.get("/history")
def get_history(
    status_filter: str | None = None,
    job_title: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Resume)
    if status_filter and status_filter != "All":
        query = query.filter(Resume.status == status_filter)
    if job_title and job_title != "All":
        query = query.filter(Resume.job_title == job_title)

    records = query.order_by(Resume.ats_score.desc(), Resume.created_at.desc()).all()
    return {"total": len(records), "results": [serialize_record(r) for r in records]}


@router.get("/history/{resume_id}")
def get_screening_details(resume_id: int, db: Session = Depends(get_db)):
    record = db.query(Resume).filter(Resume.id == resume_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Screening not found.")
    return {"screening": serialize_record(record, include_text=True)}


@router.patch("/history/{resume_id}")
def update_candidate(
    resume_id: int,
    status: str | None = Form(None),
    recruiter_notes: str | None = Form(None),
    db: Session = Depends(get_db),
):
    record = db.query(Resume).filter(Resume.id == resume_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    if status is not None:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Use: {sorted(VALID_STATUSES)}")
        record.status = status

    if recruiter_notes is not None:
        record.recruiter_notes = recruiter_notes.strip()

    db.commit()
    db.refresh(record)
    return {"success": True, "candidate": serialize_record(record)}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    records = db.query(Resume).all()
    scores = [float(r.ats_score or 0) for r in records]
    status_counts = {status: 0 for status in sorted(VALID_STATUSES)}
    skill_counts = {}

    for record in records:
        status_counts[record.status or "Review"] = status_counts.get(record.status or "Review", 0) + 1
        for skill in safe_json(record.matched_skills):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "total_screened": len(records),
        "shortlisted": status_counts.get("Shortlisted", 0),
        "average_fit_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "status_counts": status_counts,
        "top_matched_skills": [{"skill": skill, "count": count} for skill, count in top_skills],
    }
