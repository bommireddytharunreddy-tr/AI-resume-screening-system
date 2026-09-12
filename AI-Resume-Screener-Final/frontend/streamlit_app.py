from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.api import APIError, create_job, delete_job, get_candidate, get_dashboard, get_history, get_jobs, get_status, screen_resume, update_candidate  # noqa: E402


st.set_page_config(
    page_title="TalentLens | AI Resume Screener",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
st.markdown(
    """
<style>
:root { --ink:#182230; --muted:#667085; --line:#e7eaf0; --surface:#ffffff; --soft:#f6f8fb; }
.stApp { background:#f7f8fb; color:var(--ink); }
section[data-testid="stSidebar"] { background:#111827; }
section[data-testid="stSidebar"] * { color:#eef2f7 !important; }
.block-container { padding-top:2rem; padding-bottom:3rem; max-width:1450px; }
.hero { padding:1.2rem 0 1.8rem 0; }
.hero h1 { font-size:2.25rem; margin:0; letter-spacing:-.04em; }
.hero p { color:var(--muted); margin:.4rem 0 0; font-size:1.02rem; }
.card { background:white; border:1px solid var(--line); border-radius:16px; padding:20px; box-shadow:0 5px 18px rgba(16,24,40,.04); }
.kpi { background:white; border:1px solid var(--line); border-radius:14px; padding:18px 20px; }
.kpi-label { color:var(--muted); font-size:.82rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
.kpi-value { font-size:1.9rem; font-weight:750; margin-top:.2rem; }
.muted { color:var(--muted); }
.tag { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:4px 10px; margin:2px 4px 2px 0; font-size:.78rem; background:#fafbfc; }
.score { font-size:3.2rem; line-height:1; font-weight:800; }
.small-note { font-size:.78rem; color:var(--muted); }
</style>
""",
    unsafe_allow_html=True,
)

if "api_url" not in st.session_state:
    st.session_state.api_url = "https://talentlens-api-6ke6.onrender.com"
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None


def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except APIError as exc:
        st.error(str(exc))
        return None


def score_label(score):
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Shortlist"
    if score >= 55:
        return "Review"
    return "Low Match"


def tag_html(values):
    if not values:
        return '<span class="muted">None detected</span>'
    return "".join(f'<span class="tag">{str(v).title()}</span>' for v in values)


def candidate_table(records):
    if not records:
        st.info("No candidates match the current filters.")
        return
    rows = []
    for r in records:
        a = r["analysis"]
        rows.append(
            {
                "ID": r["id"],
                "Candidate": r["candidate_name"],
                "Job": r["job_title"] or "General screening",
                "Fit": a["fit_score"],
                "Skills": a["skills_match_score"],
                "Semantic": a["semantic_similarity_score"],
                "Status": r["status"],
                "Email": r["email"],
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fit": st.column_config.ProgressColumn("AI Fit", min_value=0, max_value=100, format="%.1f"),
            "Skills": st.column_config.NumberColumn(format="%.1f"),
            "Semantic": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.caption("AI scores are decision-support signals. Final hiring decisions remain with qualified recruiters.")


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ◈ TalentLens")
    st.caption("Recruiter Screening Workspace")
    st.divider()

    pages = {
        "Dashboard": "Overview",
        "Screen Resumes": "Screen Resumes",
        "Candidates": "Candidate Pool",
        "Jobs": "Job Profiles",
        "Analytics": "Analytics",
    }
    for key, label in pages.items():
        if st.button(label, use_container_width=True, type="secondary" if st.session_state.page != key else "primary"):
            st.session_state.page = key
            st.session_state.selected_candidate = None
            st.rerun()

    st.divider()
    st.caption("Backend")
    st.session_state.api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        label_visibility="collapsed",
    ).rstrip("/")
    health = safe_call(get_status, st.session_state.api_url)
    if health:
        st.success("Connected")
    else:
        st.error("Offline")

    st.divider()
    st.caption("Responsible use")
    st.caption("AI assists screening. It should not be used as the sole basis for employment decisions.")


# ---------- Candidate detail ----------
def render_candidate_detail(candidate_id):
    detail = safe_call(get_candidate, st.session_state.api_url, candidate_id)
    if not detail:
        return
    c = detail["screening"]
    a = c["analysis"]
    skills = c["skills"]
    profile = c["profile"]

    if st.button("← Back to candidates"):
        st.session_state.selected_candidate = None
        st.rerun()

    st.markdown(f'<div class="hero"><h1>{c["candidate_name"]}</h1><p>{c["job_title"] or "General screening"} · {c["filename"]}</p></div>', unsafe_allow_html=True)

    cols = st.columns(4)
    metrics = [
        ("AI Fit Score", f'{a["fit_score"]:.1f}%'),
        ("Skills Match", f'{a["skills_match_score"]:.1f}%'),
        ("Semantic Match", f'{a["semantic_similarity_score"]:.1f}%'),
        ("Recommendation", a["recommendation"]),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.25, .75])

    with left:
        st.markdown("### Match evidence")
        st.markdown("**Matched skills**")
        st.markdown(tag_html(skills["matched_skills"]), unsafe_allow_html=True)
        st.markdown("**Missing / not detected**")
        st.markdown(tag_html(skills["missing_skills"]), unsafe_allow_html=True)

        st.markdown("### Profile")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("**Contact**")
            st.write(c["email"] or "Email not detected")
            st.write(c["phone"] or "Phone not detected")
        with p2:
            st.markdown("**Education signals**")
            st.write(", ".join(profile["education"]) if profile["education"] else "Not clearly detected")
            st.markdown("**Experience signals**")
            st.write(", ".join(profile["experience"]) if profile["experience"] else "Not clearly detected")

        with st.expander("View extracted resume text"):
            st.text(c.get("resume_text", ""))

        with st.expander("View job description used for matching"):
            st.text(c.get("job_description", ""))

    with right:
        st.markdown("### Recruiter decision")
        status_options = ["Review", "Shortlisted", "On Hold", "Rejected"]
        current_index = status_options.index(c["status"]) if c["status"] in status_options else 0
        status = st.selectbox("Candidate status", status_options, index=current_index)
        notes = st.text_area("Recruiter notes", value=c.get("recruiter_notes", ""), height=180)
        if st.button("Save candidate", type="primary", use_container_width=True):
            result = safe_call(update_candidate, st.session_state.api_url, c["id"], status, notes)
            if result:
                st.success("Candidate record updated.")
                st.rerun()

        st.markdown("### AI review notes")
        for suggestion in c["suggestions"]:
            st.info(suggestion)


# ---------- Pages ----------
page = st.session_state.page

if st.session_state.selected_candidate:
    render_candidate_detail(st.session_state.selected_candidate)

elif page == "Dashboard":
    st.markdown('<div class="hero"><h1>Recruiter Dashboard</h1><p>Screen faster, compare candidates consistently, and keep the human decision-maker in control.</p></div>', unsafe_allow_html=True)
    dash = safe_call(get_dashboard, st.session_state.api_url)
    if dash:
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            ("Resumes screened", dash["total_screened"]),
            ("Shortlisted", dash["shortlisted"]),
            ("Average AI fit", f'{dash["average_fit_score"]:.1f}%'),
            ("Active workflow", sum(dash["status_counts"].values())),
        ]
        for col, (label, value) in zip([c1, c2, c3, c4], kpis):
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

        st.write("")
        left, right = st.columns([1.2, .8])
        with left:
            st.markdown("### Recent candidate ranking")
            history = safe_call(get_history, st.session_state.api_url)
            if history:
                candidate_table(history["results"][:8])
                if history["results"]:
                    selected = st.selectbox(
                        "Open candidate",
                        ["Select a candidate"] + [
                            f'{r["id"]} · {r["candidate_name"]} · {r["analysis"]["fit_score"]:.1f}%'
                            for r in history["results"][:8]
                        ],
                    )
                    if selected != "Select a candidate":
                        st.session_state.selected_candidate = int(selected.split(" · ")[0])
                        st.rerun()
        with right:
            st.markdown("### Workflow status")
            status_df = pd.DataFrame(
                [{"Status": k, "Candidates": v} for k, v in dash["status_counts"].items()]
            )
            fig = px.bar(status_df, x="Status", y="Candidates", text="Candidates")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=310)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Top matched skills")
            if dash["top_matched_skills"]:
                st.dataframe(
                    pd.DataFrame(dash["top_matched_skills"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Screen a few resumes to populate recruiter analytics.")

elif page == "Screen Resumes":
    st.markdown('<div class="hero"><h1>Screen Resumes</h1><p>Upload one or more resumes against a selected job profile. Each file is evaluated independently.</p></div>', unsafe_allow_html=True)
    jobs = safe_call(get_jobs, st.session_state.api_url) or []

    if jobs:
        labels = {f'{j["title"]} · {j.get("department") or "General"}': j for j in jobs}
        choice = st.selectbox("Job profile", list(labels.keys()))
        selected_job = labels[choice]
        job_title = selected_job["title"]
        job_description = selected_job["description"]
        with st.expander("Review job requirements before screening"):
            st.write(job_description)
    else:
        st.warning("Create a job profile first. This prevents screening candidates against an unclear or inconsistent requirement set.")
        job_title = st.text_input("Job title")
        job_description = st.text_area("Job description", height=220, placeholder="Include responsibilities, required skills, preferred skills and experience.")

    uploads = st.file_uploader(
        "Upload resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="PDF and DOCX are supported. Avoid uploading files containing unnecessary sensitive information.",
    )

    if uploads:
        st.caption(f"{len(uploads)} resume(s) ready for screening.")
        if st.button("Run AI screening", type="primary", use_container_width=True):
            if not job_title.strip() or not job_description.strip():
                st.error("Provide a job title and a complete job description.")
            else:
                progress = st.progress(0)
                results = []
                for i, upload in enumerate(uploads, start=1):
                    with st.status(f"Screening {upload.name}...", expanded=False) as status:
                        result = safe_call(
                            screen_resume,
                            st.session_state.api_url,
                            upload,
                            job_description,
                            job_title,
                        )
                        if result:
                            results.append(result)
                            status.update(label=f"Completed: {upload.name}", state="complete")
                        else:
                            status.update(label=f"Failed: {upload.name}", state="error")
                    progress.progress(i / len(uploads))

                if results:
                    st.session_state.last_result = results
                    st.success(f"Screened {len(results)} resume(s).")
                    st.markdown("### Screening results")
                    rows = []
                    for r in results:
                        a = r["analysis"]
                        rows.append({
                            "ID": r["id"],
                            "Candidate": r["candidate_name"],
                            "AI Fit": a["fit_score"],
                            "Skills Match": a["skills_match_score"],
                            "Recommendation": a["recommendation"],
                            "Status": r["status"],
                        })
                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "AI Fit": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                            "Skills Match": st.column_config.NumberColumn(format="%.1f%%"),
                        },
                    )

elif page == "Candidates":
    st.markdown('<div class="hero"><h1>Candidate Pool</h1><p>Search, filter and open individual screening records for human review.</p></div>', unsafe_allow_html=True)
    history = safe_call(get_history, st.session_state.api_url)
    if history:
        records = history["results"]
        jobs = sorted({r["job_title"] for r in records if r["job_title"]})
        f1, f2, f3 = st.columns([1, 1, 1.5])
        with f1:
            status_filter = st.selectbox("Status", ["All", "Shortlisted", "Review", "On Hold", "Rejected"])
        with f2:
            job_filter = st.selectbox("Job", ["All"] + jobs)
        with f3:
            search = st.text_input("Search candidate", placeholder="Name or email")
        filtered = [
            r for r in records
            if (status_filter == "All" or r["status"] == status_filter)
            and (job_filter == "All" or r["job_title"] == job_filter)
            and (not search.strip() or search.lower() in (r["candidate_name"] + " " + r["email"]).lower())
        ]
        candidate_table(filtered)
        if filtered:
            st.markdown("### Open candidate")
            options = {
                f'{r["candidate_name"]} · {r["analysis"]["fit_score"]:.1f}% · {r["status"]}': r["id"]
                for r in filtered
            }
            picked = st.selectbox("Candidate", list(options.keys()))
            if st.button("Open candidate profile", type="primary"):
                st.session_state.selected_candidate = options[picked]
                st.rerun()

elif page == "Jobs":
    st.markdown('<div class="hero"><h1>Job Profiles</h1><p>Maintain consistent job requirements so every candidate is evaluated against the same role definition.</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.25])
    with left:
        st.markdown("### Create a job profile")
        with st.form("job_form", clear_on_submit=True):
            title = st.text_input("Job title *")
            department = st.text_input("Department")
            location = st.text_input("Location")
            description = st.text_area(
                "Job description *",
                height=300,
                placeholder="Responsibilities\nRequired skills\nPreferred skills\nExperience\nEducation",
            )
            submitted = st.form_submit_button("Save job profile", type="primary", use_container_width=True)
            if submitted:
                result = safe_call(create_job, st.session_state.api_url, title, description, location, department)
                if result:
                    st.success("Job profile saved.")
                    st.rerun()
    with right:
        st.markdown("### Saved job profiles")
        jobs = safe_call(get_jobs, st.session_state.api_url) or []
        if not jobs:
            st.info("No job profiles yet.")
        for job in jobs:
            with st.container(border=True):
                st.markdown(f"**{job['title']}**")
                st.caption(" · ".join(x for x in [job.get("department"), job.get("location")] if x) or "General")
                st.write(job["description"][:500] + ("…" if len(job["description"]) > 500 else ""))
                if st.button("Delete", key=f"delete_job_{job['id']}"):
                    if safe_call(delete_job, st.session_state.api_url, job["id"]) is not None:
                        st.rerun()

elif page == "Analytics":
    st.markdown('<div class="hero"><h1>Screening Analytics</h1><p>Understand candidate quality and workflow volume without replacing recruiter judgment.</p></div>', unsafe_allow_html=True)
    history = safe_call(get_history, st.session_state.api_url)
    if history and history["results"]:
        records = history["results"]
        df = pd.DataFrame([
            {
                "Candidate": r["candidate_name"],
                "Fit": r["analysis"]["fit_score"],
                "Skills": r["analysis"]["skills_match_score"],
                "Semantic": r["analysis"]["semantic_similarity_score"],
                "Completeness": r["analysis"]["resume_completeness_score"],
                "Status": r["status"],
                "Job": r["job_title"] or "General",
            }
            for r in records
        ])
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(df, x="Fit", nbins=10, title="AI fit score distribution")
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), height=340)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            avg = df.groupby("Status", as_index=False)["Fit"].mean()
            fig = px.bar(avg, x="Status", y="Fit", text_auto=".1f", title="Average fit by workflow status")
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), height=340)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Export screening data")
        export_df = df.copy()
        st.download_button(
            "Download CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="candidate_screening_report.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.info("Screen resumes to generate analytics.")


st.markdown(
    "<hr><div class='small-note'>TalentLens is a screening assistant. Extraction and matching can be imperfect; recruiters should verify resumes and apply consistent, lawful hiring criteria.</div>",
    unsafe_allow_html=True,
)
