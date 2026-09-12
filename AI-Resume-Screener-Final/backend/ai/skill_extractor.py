import re


class SkillExtractor:

    SKILLS = [
        # Programming Languages
        "python",
        "java",
        "c",
        "c++",
        "c#",
        "javascript",
        "typescript",
        "go",
        "golang",
        "rust",
        "php",

        # Web Development
        "html",
        "css",
        "react",
        "react.js",
        "angular",
        "vue",
        "node.js",
        "node",
        "express",
        "next.js",
        "nextjs",

        # Backend
        "fastapi",
        "django",
        "flask",
        "spring boot",
        "spring",

        # Databases
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "sqlite",
        "oracle",
        "redis",

        # AI / ML
        "artificial intelligence",
        "ai",
        "machine learning",
        "deep learning",
        "natural language processing",
        "nlp",
        "computer vision",
        "generative ai",

        # ML Libraries
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "sklearn",
        "keras",
        "opencv",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",

        # Cloud
        "aws",
        "amazon web services",
        "azure",
        "google cloud",
        "gcp",

        # DevOps
        "docker",
        "kubernetes",
        "jenkins",
        "ci/cd",

        # Tools
        "git",
        "github",
        "gitlab",
        "linux",
        "rest api",
        "restful api",
        "api",

        # Data
        "data analysis",
        "data science",
        "data visualization",
        "statistics",
        "excel",

        # Other
        "power bi",
        "tableau",
        "firebase",
        "figma"
    ]

    @classmethod
    def extract(cls, text: str) -> list[str]:

        if not text:
            return []

        text = text.lower()

        found_skills = set()

        for skill in cls.SKILLS:

            # Escape special regex characters
            pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"

            if re.search(pattern, text):
                found_skills.add(skill)

        return sorted(found_skills)