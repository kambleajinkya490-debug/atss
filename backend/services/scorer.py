import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter


TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue", "node",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn",
    "fastapi", "flask", "django", "spring", "express", "graphql", "rest", "api",
    "git", "ci/cd", "agile", "scrum", "devops", "linux", "bash",
    "data science", "analytics", "tableau", "power bi", "spark", "hadoop",
    "c++", "c#", "go", "rust", "ruby", "php", "scala", "kotlin", "swift",
    "html", "css", "sass", "webpack", "microservices", "kafka", "rabbitmq",
    "pandas", "numpy", "matplotlib", "seaborn", "excel", "r", "matlab",
    "blockchain", "cybersecurity", "networking", "cloud", "serverless",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "problem-solving", "analytical",
    "critical thinking", "project management", "collaboration", "adaptability",
    "creativity", "time management", "mentoring", "presentation", "negotiation",
    "strategic", "innovative", "detail-oriented", "self-motivated", "proactive",
}

EDUCATION_KEYWORDS = {
    "bachelor", "master", "phd", "doctorate", "degree", "computer science",
    "engineering", "mathematics", "statistics", "mba", "bs", "ms", "ba", "ma",
    "university", "college", "institute", "certification", "certified",
}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\-\.]*\b', text)
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)]
    return tokens + bigrams


def compute_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_features=5000)
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(float(similarity), 4)
    except Exception:
        return 0.0


def extract_keywords(text: str, top_n: int = 50) -> list[str]:
    text_lower = text.lower()
    found = set()
    for skill in TECH_SKILLS | SOFT_SKILLS | EDUCATION_KEYWORDS:
        if skill in text_lower:
            found.add(skill)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_features=200)
    try:
        tfidf = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf.toarray()[0]
        top_indices = scores.argsort()[-top_n:][::-1]
        for idx in top_indices:
            word = feature_names[idx]
            if len(word) > 2 and scores[idx] > 0:
                found.add(word)
    except Exception:
        pass
    return list(found)[:top_n]


def compute_keyword_match(resume_text: str, jd_text: str) -> dict:
    jd_keywords = extract_keywords(jd_text, top_n=60)
    resume_lower = resume_text.lower()
    matched = []
    missing = []
    for kw in jd_keywords:
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)
    total = len(jd_keywords) if jd_keywords else 1
    score = len(matched) / total
    return {
        "score": round(score, 4),
        "matched": matched,
        "missing": missing[:20],
        "total_jd_keywords": len(jd_keywords)
    }


def compute_skills_match(resume_text: str, jd_text: str) -> dict:
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    all_skills = TECH_SKILLS | SOFT_SKILLS
    jd_skills = [s for s in all_skills if s in jd_lower]
    if not jd_skills:
        return {"score": 0.5, "matched_skills": [], "missing_skills": []}
    matched = [s for s in jd_skills if s in resume_lower]
    missing = [s for s in jd_skills if s not in resume_lower]
    score = len(matched) / len(jd_skills)
    return {
        "score": round(score, 4),
        "matched_skills": matched,
        "missing_skills": missing[:15]
    }


def compute_experience_relevance(resume_text: str, jd_text: str) -> dict:
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
        r'(\d+)\+?\s*yrs?\s*(?:of\s+)?experience',
    ]
    resume_years = 0
    for pat in experience_patterns:
        matches = re.findall(pat, resume_text.lower())
        if matches:
            resume_years = max(int(m) for m in matches)
            break
    jd_years_required = 0
    for pat in experience_patterns:
        matches = re.findall(pat, jd_text.lower())
        if matches:
            jd_years_required = max(int(m) for m in matches)
            break
    tfidf_score = compute_tfidf_similarity(resume_text, jd_text)
    if jd_years_required > 0:
        year_score = min(resume_years / jd_years_required, 1.0)
    else:
        year_score = 0.7
    combined = (tfidf_score * 0.7 + year_score * 0.3)
    return {
        "score": round(min(combined, 1.0), 4),
        "resume_years": resume_years,
        "required_years": jd_years_required,
        "content_similarity": round(tfidf_score, 4)
    }


def compute_education_match(resume_text: str, jd_text: str) -> dict:
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    jd_edu = [kw for kw in EDUCATION_KEYWORDS if kw in jd_lower]
    if not jd_edu:
        return {"score": 0.75, "details": "No specific education requirements found"}
    matched = [kw for kw in jd_edu if kw in resume_lower]
    score = len(matched) / len(jd_edu) if jd_edu else 0.75
    return {
        "score": round(min(score * 1.2, 1.0), 4),
        "required": jd_edu,
        "matched": matched
    }


def compute_formatting_score(resume_text: str) -> dict:
    score = 0.5
    details = []
    word_count = len(resume_text.split())
    if 300 <= word_count <= 1000:
        score += 0.15
        details.append("Good length")
    elif word_count < 300:
        details.append("Resume may be too short")
    else:
        details.append("Resume may be too long")
    sections = ["experience", "education", "skills", "summary", "objective", "projects"]
    found_sections = [s for s in sections if s in resume_text.lower()]
    section_score = len(found_sections) / len(sections)
    score += section_score * 0.2
    details.append(f"Found {len(found_sections)} standard sections")
    bullet_count = resume_text.count('•') + resume_text.count('·') + resume_text.count('-')
    if bullet_count > 5:
        score += 0.1
        details.append("Good use of bullet points")
    if not re.search(r'[A-Z]{5,}', resume_text):
        score += 0.05
        details.append("Good capitalization")
    return {
        "score": round(min(score, 1.0), 4),
        "word_count": word_count,
        "sections_found": found_sections,
        "details": details
    }
