# TalentLens — AI Resume Screener

A recruiter-focused AI resume screening platform built with **Python, FastAPI, Streamlit, SQLAlchemy, SQLite, scikit-learn and Sentence Transformers**.

The original project was extended into a practical screening workspace rather than a simple "upload → score" demo.

## What it does

- Create and save job profiles.
- Upload one or many PDF/DOCX resumes.
- Extract candidate name, email, phone, education and experience signals.
- Extract technical skills.
- Compare resume skills with job requirements.
- Calculate semantic similarity using `all-MiniLM-L6-v2`, with TF-IDF fallback.
- Produce an explainable **AI Fit Score**.
- Rank candidates by fit.
- Filter candidates by job/status.
- Open a detailed candidate profile.
- Add recruiter notes and change workflow status.
- View screening analytics.
- Export screening results to CSV.
- Preserve records in SQLite.

## Important scoring note

The displayed **AI Fit Score is a project-specific decision-support score, not a universal ATS score**.

Current weighting:

- 50% required-skill alignment
- 35% semantic similarity
- 15% resume completeness

The application deliberately keeps the recommendation explainable so a recruiter can inspect the underlying signals.

## Architecture

```text
                         ┌─────────────────────────┐
                         │   Streamlit Recruiter UI │
                         │ Dashboard / Jobs /       │
                         │ Screening / Candidates   │
                         └────────────┬────────────┘
                                      │ HTTP
                         ┌────────────▼────────────┐
                         │      FastAPI API         │
                         │ Jobs / Screening /       │
                         │ Candidate workflow       │
                         └────────────┬────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
      Resume Parser             AI Matching              SQLite DB
      PDF / DOCX                Skills + Semantic       Jobs + Candidates
             │                  Similarity + Score
             └────────────────────────┼────────────────────────┘
                                      │
                              Recruiter review
```

## Project structure

```text
AI-Resume-Screener/
├── backend/
│   ├── ai/
│   │   ├── ats_score.py
│   │   ├── parser.py
│   │   ├── preprocess.py
│   │   ├── profile_extractor.py
│   │   ├── similarity.py
│   │   ├── skill_extractor.py
│   │   └── suggestions.py
│   ├── routes/
│   │   └── resume.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── requirements.txt
├── frontend/
│   ├── api.py
│   └── streamlit_app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Windows setup

Open a terminal in the project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start the API in terminal 1:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Start Streamlit in terminal 2:

```powershell
streamlit run frontend/streamlit_app.py
```

Open the Streamlit URL shown in the terminal.

### First AI-model run

Sentence Transformers may download the `all-MiniLM-L6-v2` model on its first use. This is normal. If the model cannot load, the matching module automatically falls back to TF-IDF similarity.

## Recommended demo flow

1. Open **Jobs**.
2. Create a realistic role, e.g. `Python Backend Developer`.
3. Include required and preferred skills in the job description.
4. Open **Screen Resumes**.
5. Upload several resumes together.
6. Run screening.
7. Open **Candidates** and compare the ranking.
8. Open a candidate to inspect matched/missing skills.
9. Change status to `Shortlisted`, `On Hold`, `Rejected`, or `Review`.
10. Add a recruiter note.
11. Open **Analytics** and export the report.

## GitHub hygiene

Do **not** commit:

- `.venv/`
- `backend/venv/`
- `backend/resume.db`
- uploaded resumes
- `__pycache__/`
- `.env`
- local model/cache folders

The final deliverable intentionally excludes the original virtual environment, local database and uploaded resumes.

## Responsible-use boundary

This application is designed as recruiter decision support. Resume parsing and similarity matching can make mistakes and may encode bias from data or job requirements. Recruiters should verify candidate information, use job-relevant criteria, and avoid using the model as the sole basis for employment decisions.
