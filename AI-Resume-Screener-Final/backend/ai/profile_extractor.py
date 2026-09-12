import re


class ProfileExtractor:
    """Lightweight, explainable profile extraction for recruiter review."""

    EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)")
    YEARS_RE = re.compile(
        r"\b(\d+(?:\.\d+)?)\+?\s*(years?|yrs?)\s*(?:of\s*)?experience\b",
        re.I,
    )
    MONTHS_RE = re.compile(
        r"\b(\d+)\+?\s*(months?|mos?)\s*(?:of\s*)?experience\b",
        re.I,
    )

    EDUCATION_TERMS = [
        "b.tech", "btech", "b.e", "be", "b.sc", "bsc", "b.com", "bcom",
        "b.a", "ba", "bca", "m.tech", "mtech", "m.e", "me", "m.sc", "msc",
        "mca", "mba", "ph.d", "phd", "bachelor", "master", "university",
        "college", "computer science", "information technology",
        "software engineering",
    ]

    ROLE_TERMS = [
        "software engineer", "software developer", "python developer",
        "java developer", "web developer", "frontend developer",
        "backend developer", "full stack developer", "data scientist",
        "data analyst", "data engineer", "machine learning engineer",
        "ai engineer", "devops engineer", "intern", "developer", "engineer",
    ]

    @classmethod
    def extract_contact(cls, text: str) -> dict:
        email = cls.EMAIL_RE.search(text)
        phone = cls.PHONE_RE.search(text)
        return {
            "email": email.group(0) if email else "",
            "phone": cls._clean_phone(phone.group(0)) if phone else "",
        }

    @staticmethod
    def _clean_phone(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @classmethod
    def extract_candidate_name(cls, text: str) -> str:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        for line in lines[:12]:
            match = re.match(r"^(?:name)\s*[:\-]\s*(.+)$", line, re.I)
            if match:
                candidate = match.group(1).strip()
                if 1 < len(candidate.split()) <= 5:
                    return candidate

        excluded = {
            "resume", "curriculum vitae", "cv", "profile", "summary",
            "objective", "experience", "education", "skills",
        }
        for line in lines[:8]:
            if len(line.split()) <= 5 and line.lower() not in excluded:
                if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,60}", line):
                    return line

        return "Unknown candidate"

    @classmethod
    def extract_education(cls, text: str) -> list[str]:
        found = []
        for term in cls.EDUCATION_TERMS:
            if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I):
                found.append(term)
        return sorted(set(found), key=str.lower)

    @classmethod
    def extract_experience(cls, text: str) -> list[str]:
        found = []
        for match in cls.YEARS_RE.finditer(text):
            found.append(match.group(0))
        for match in cls.MONTHS_RE.finditer(text):
            found.append(match.group(0))

        lower = text.lower()
        for role in cls.ROLE_TERMS:
            if re.search(r"(?<!\w)" + re.escape(role) + r"(?!\w)", lower):
                found.append(role)

        return list(dict.fromkeys(found))

    @classmethod
    def extract_profile(cls, text: str) -> dict:
        contact = cls.extract_contact(text)
        return {
            "name": cls.extract_candidate_name(text),
            "email": contact["email"],
            "phone": contact["phone"],
            "education": cls.extract_education(text),
            "experience": cls.extract_experience(text),
        }
