from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def _load_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


class ResumeSimilarity:
    """Semantic matching with a safe TF-IDF fallback."""

    @staticmethod
    def calculate(resume_text: str, job_description: str) -> float:
        resume_text = (resume_text or "").strip()
        job_description = (job_description or "").strip()

        if not resume_text or not job_description:
            return 0.0

        model = _load_embedding_model()
        if model is not None:
            try:
                embeddings = model.encode(
                    [resume_text, job_description],
                    normalize_embeddings=True,
                )
                score = float(embeddings[0] @ embeddings[1]) * 100
                return round(max(0.0, min(score, 100.0)), 2)
            except Exception:
                pass

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            matrix = vectorizer.fit_transform([resume_text, job_description])
            score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0]) * 100
            return round(max(0.0, min(score, 100.0)), 2)
        except Exception:
            return 0.0
