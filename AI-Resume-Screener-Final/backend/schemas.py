from pydantic import BaseModel


class ResumeResponse(BaseModel):

    filename: str

    extracted_text: str

    skills: list[str]

    ats_score: float

    class Config:
        from_attributes = True