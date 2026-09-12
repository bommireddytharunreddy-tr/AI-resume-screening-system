import requests

DEFAULT_API_URL = "http://127.0.0.1:8000"


class APIError(RuntimeError):
    pass


def _request(method, url, **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise APIError(
            "Backend is not reachable. Start FastAPI with "
            "`uvicorn backend.main:app --reload --port 8000`."
        ) from exc

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise APIError(str(detail))

    return response.json()


def get_status(base_url):
    return _request("GET", f"{base_url}/status", timeout=10)


def get_dashboard(base_url):
    return _request("GET", f"{base_url}/dashboard")


def get_jobs(base_url):
    return _request("GET", f"{base_url}/jobs")


def create_job(base_url, title, description, location="", department=""):
    return _request(
        "POST",
        f"{base_url}/jobs",
        data={
            "title": title,
            "description": description,
            "location": location,
            "department": department,
        },
    )


def delete_job(base_url, job_id):
    return _request("DELETE", f"{base_url}/jobs/{job_id}")


def screen_resume(base_url, uploaded_file, job_description, job_title):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    return _request(
        "POST",
        f"{base_url}/analyze",
        files=files,
        data={"job_description": job_description, "job_title": job_title},
    )


def get_history(base_url, status_filter="All", job_title="All"):
    return _request(
        "GET",
        f"{base_url}/history",
        params={"status_filter": status_filter, "job_title": job_title},
    )


def get_candidate(base_url, candidate_id):
    return _request("GET", f"{base_url}/history/{candidate_id}")


def update_candidate(base_url, candidate_id, status, notes):
    return _request(
        "PATCH",
        f"{base_url}/history/{candidate_id}",
        data={"status": status, "recruiter_notes": notes},
    )
