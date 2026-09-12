class ResumeSuggestions:

    @staticmethod
    def generate(
        resume_text: str,
        resume_skills: list[str],
        missing_skills: list[str]
    ) -> list[str]:

        suggestions = []

        text = resume_text.lower()

        # ---------------------------------------
        # Missing skills
        # ---------------------------------------

        if missing_skills:

            skills = ", ".join(
                missing_skills[:5]
            )

            suggestions.append(
                f"Consider adding relevant experience or projects "
                f"related to these job requirements: {skills}."
            )

        # ---------------------------------------
        # Contact information
        # ---------------------------------------

        if "@" not in text:

            suggestions.append(
                "Add a professional email address to your resume."
            )

        # ---------------------------------------
        # Education
        # ---------------------------------------

        if "education" not in text:

            suggestions.append(
                "Add an Education section containing your degree, "
                "institution and graduation details."
            )

        # ---------------------------------------
        # Experience
        # ---------------------------------------

        if "experience" not in text:

            suggestions.append(
                "Add an Experience section describing internships, "
                "training or relevant professional experience."
            )

        # ---------------------------------------
        # Projects
        # ---------------------------------------

        if "project" not in text:

            suggestions.append(
                "Add relevant technical projects and briefly "
                "describe the technologies and your contribution."
            )

        # ---------------------------------------
        # Skills
        # ---------------------------------------

        if "skill" not in text:

            suggestions.append(
                "Add a dedicated Skills section containing "
                "your relevant technical skills."
            )

        # ---------------------------------------
        # Certifications
        # ---------------------------------------

        if "certification" not in text:

            suggestions.append(
                "Consider adding relevant certifications, "
                "courses or professional training."
            )

        # ---------------------------------------
        # Quantifiable achievements
        # ---------------------------------------

        achievement_words = [
            "%",
            "increased",
            "decreased",
            "improved",
            "reduced",
            "achieved",
            "developed",
            "implemented"
        ]

        has_achievement = any(
            word in text
            for word in achievement_words
        )

        if not has_achievement:

            suggestions.append(
                "Use measurable achievements where possible, "
                "such as percentages, numbers or performance improvements."
            )

        # ---------------------------------------
        # Resume length/content
        # ---------------------------------------

        word_count = len(
            resume_text.split()
        )

        if word_count < 150:

            suggestions.append(
                "Your resume appears to contain limited content. "
                "Consider adding relevant projects, experience and achievements."
            )

        # ---------------------------------------
        # No suggestions
        # ---------------------------------------

        if not suggestions:

            suggestions.append(
                "Your resume covers the major sections well. "
                "Continue tailoring it to each job description."
            )

        return suggestions