import fitz
from docx import Document


class ResumeParser:

    @staticmethod
    def extract_pdf_text(file_path: str) -> str:
        text = ""

        document = fitz.open(file_path)

        for page in document:
            text += page.get_text()

        document.close()

        return text.strip()

    @staticmethod
    def extract_docx_text(file_path: str) -> str:
        document = Document(file_path)

        text = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text.strip())

        return "\n".join(text)

    @staticmethod
    def extract_text(file_path: str) -> str:
        file_path_lower = file_path.lower()

        if file_path_lower.endswith(".pdf"):
            return ResumeParser.extract_pdf_text(file_path)

        if file_path_lower.endswith(".docx"):
            return ResumeParser.extract_docx_text(file_path)

        raise ValueError("Only PDF and DOCX files are supported.")