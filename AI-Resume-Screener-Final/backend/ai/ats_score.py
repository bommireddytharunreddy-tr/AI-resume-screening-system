class ATSScore:

    @staticmethod
    def calculate(
        resume_text: str,
        resume_skills: list[str],
        required_skills: list[str],
        similarity_score: float
    ):

        resume_text_lower = resume_text.lower()

        # ---------------------------------------
        # Matched skills
        # ---------------------------------------

        matched_skills = [
            skill
            for skill in required_skills
            if skill.lower() in resume_text_lower
        ]

        # ---------------------------------------
        # Missing skills
        # ---------------------------------------

        missing_skills = [
            skill
            for skill in required_skills
            if skill.lower() not in resume_text_lower
        ]

        # ---------------------------------------
        # Skills match score
        # ---------------------------------------

        if required_skills:

            skills_match_score = (
                len(matched_skills)
                / len(required_skills)
            ) * 100

        else:

            skills_match_score = 100.0

        # ---------------------------------------
        # Resume completeness
        # ---------------------------------------

        text = resume_text_lower

        sections = [
            "education",
            "experience",
            "skills",
            "project"
        ]

        found_sections = sum(
            1
            for section in sections
            if section in text
        )

        completeness_score = (
            found_sections
            / len(sections)
        ) * 100

        # ---------------------------------------
        # Final ATS score
        # ---------------------------------------

        ats_score = (
            (float(similarity_score) * 0.40)
            + (float(skills_match_score) * 0.40)
            + (float(completeness_score) * 0.20)
        )

        return {

            "ats_score": round(
                float(ats_score),
                2
            ),

            "similarity_score": round(
                float(similarity_score),
                2
            ),

            "skills_match_score": round(
                float(skills_match_score),
                2
            ),

            "completeness_score": round(
                float(completeness_score),
                2
            ),

            "matched_skills": matched_skills,

            "missing_skills": missing_skills
        }