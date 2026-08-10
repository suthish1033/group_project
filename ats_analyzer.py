import re


JOB_ROLES = {

    "Python Developer": [
        "python",
        "django",
        "flask",
        "sql",
        "git",
        "rest api",
        "mongodb",
        "api"
    ],

    "Data Scientist": [
        "python",
        "machine learning",
        "pandas",
        "numpy",
        "scikit-learn",
        "statistics",
        "sql",
        "data analysis"
    ],

    "Data Analyst": [
        "python",
        "sql",
        "excel",
        "power bi",
        "tableau",
        "pandas",
        "data analysis",
        "statistics"
    ],

    "AI Engineer": [
        "python",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "nlp",
        "computer vision",
        "scikit-learn"
    ],

    "Web Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "python",
        "flask",
        "git",
        "rest api"
    ]
}


def calculate_ats_score(text, job_role):

    text = text.lower()

    keywords = JOB_ROLES.get(
        job_role,
        []
    )

    matched = []
    missing = []

    for keyword in keywords:

        if keyword.lower() in text:
            matched.append(keyword)
        else:
            missing.append(keyword)

    if len(keywords) > 0:

        skill_score = (
            len(matched) / len(keywords)
        ) * 70

    else:

        skill_score = 0


    # Resume section checks

    sections = {
        "education": "education" in text,
        "experience": (
            "experience" in text
            or "work experience" in text
        ),
        "projects": "project" in text,
        "skills": "skills" in text,
        "certifications": (
            "certification" in text
        )
    }


    section_score = (
        sum(sections.values()) / 5
    ) * 20


    # Basic contact check

    email_found = bool(
        re.search(
            r'[\w\.-]+@[\w\.-]+\.\w+',
            text
        )
    )

    phone_found = bool(
        re.search(
            r'\b\d{10}\b',
            text
        )
    )


    contact_score = 10 if (
        email_found and phone_found
    ) else 5 if email_found else 0


    final_score = round(
        skill_score +
        section_score +
        contact_score
    )

    final_score = min(
        final_score,
        100
    )


    # Suggestions

    suggestions = []


    if not sections["skills"]:
        suggestions.append(
            "Add a clear Skills section."
        )


    if not sections["experience"]:
        suggestions.append(
            "Add your work experience or internship details."
        )


    if not sections["projects"]:
        suggestions.append(
            "Add relevant projects."
        )


    if not sections["education"]:
        suggestions.append(
            "Add an Education section."
        )


    if missing:
        suggestions.append(
            "Consider adding relevant missing skills: "
            + ", ".join(missing[:5])
        )


    if final_score >= 80:

        status = "Excellent"

    elif final_score >= 65:

        status = "Good"

    elif final_score >= 50:

        status = "Average"

    else:

        status = "Needs Improvement"


    return {

        "score": final_score,

        "status": status,

        "job_role": job_role,

        "matched_skills": matched,

        "missing_skills": missing,

        "sections": sections,

        "email_found": email_found,

        "phone_found": phone_found,

        "suggestions": suggestions

    }