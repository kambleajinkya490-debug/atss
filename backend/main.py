import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv

from services.extractor import extract_text, clean_text
from services.scorer import (
    compute_keyword_match,
    compute_skills_match,
    compute_experience_relevance,
    compute_education_match,
    compute_formatting_score,
)
from services.ai_analyzer import analyze_with_claude
from services.report_generator import generate_pdf_report

load_dotenv()

app = FastAPI(title="ATS Resume Scorer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/ats_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_grade(score: float) -> str:
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    else:
        return "D"


def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ATS Resume Scorer API"}


@app.post("/analyze")
async def analyze_resume(
    background_tasks: BackgroundTasks,
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
):
    # Validate file type
    allowed = {".pdf", ".docx", ".doc"}
    suffix = Path(resume_file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"File type '{suffix}' not supported. Use PDF or DOCX.")

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{suffix}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(resume_file.file, buffer)
    background_tasks.add_task(cleanup_file, str(file_path))

    # Extract text
    try:
        resume_text = extract_text(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text from resume: {str(e)}")

    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Resume appears to be empty or unreadable.")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    # Clean texts
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)

    # Compute scores
    keyword_data = compute_keyword_match(resume_clean, jd_clean)
    skills_data = compute_skills_match(resume_clean, jd_clean)
    experience_data = compute_experience_relevance(resume_clean, jd_clean)
    education_data = compute_education_match(resume_clean, jd_clean)
    formatting_data = compute_formatting_score(resume_clean)

    raw_scores = {
        "keyword_score": keyword_data["score"],
        "skills_score": skills_data["score"],
        "experience_score": experience_data["score"],
        "education_score": education_data["score"],
        "formatting_score": formatting_data["score"],
    }

    # AI deep analysis
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    ai_result = {}
    if api_key:
        try:
            ai_result = analyze_with_claude(resume_clean, jd_clean, raw_scores, api_key)
            adj = ai_result.get("score_adjustments", {})
            raw_scores["keyword_score"] = min(1.0, raw_scores["keyword_score"] + adj.get("keyword_adjustment", 0) * 0.01)
            raw_scores["skills_score"] = min(1.0, raw_scores["skills_score"] + adj.get("skills_adjustment", 0) * 0.01)
            raw_scores["experience_score"] = min(1.0, raw_scores["experience_score"] + adj.get("experience_adjustment", 0) * 0.01)
        except Exception as e:
            ai_result = {
                "overall_assessment": f"AI analysis unavailable: {str(e)}",
                "top_suggestions": [],
                "strengths": [],
                "critical_gaps": []
            }
    else:
        ai_result = {
            "overall_assessment": "Set ANTHROPIC_API_KEY for AI-powered recommendations.",
            "top_suggestions": [
                {"priority": "High", "title": "Add Missing Keywords", "description": "Incorporate missing keywords from the JD naturally into your resume."},
                {"priority": "High", "title": "Quantify Achievements", "description": "Add metrics and numbers to demonstrate impact."},
                {"priority": "Medium", "title": "Tailor Your Summary", "description": "Mirror the JD's language in your professional summary."},
                {"priority": "Medium", "title": "Skills Section", "description": "List all required technologies mentioned in the job posting."},
                {"priority": "Low", "title": "Format Consistency", "description": "Use consistent formatting for better ATS parsing."},
            ],
            "strengths": ["Resume structure present", "Content included"],
            "critical_gaps": ["API key needed for full analysis"]
        }

    # Compute weighted overall score
    weights = {
        "keyword_score": 0.30,
        "skills_score": 0.25,
        "experience_score": 0.25,
        "education_score": 0.10,
        "formatting_score": 0.10,
    }
    overall = sum(raw_scores[k] * w for k, w in weights.items()) * 100

    result = {
        "overall_score": round(overall, 1),
        "grade": get_grade(overall),
        "categories": {
            "keyword_match": round(raw_scores["keyword_score"], 4),
            "skills_match": round(raw_scores["skills_score"], 4),
            "experience_relevance": round(raw_scores["experience_score"], 4),
            "education_match": round(raw_scores["education_score"], 4),
            "formatting_readability": round(raw_scores["formatting_score"], 4),
        },
        "keyword_details": {
            "matched": keyword_data["matched"][:20],
            "missing": keyword_data["missing"][:20],
            "total_jd_keywords": keyword_data["total_jd_keywords"],
        },
        "skills_details": {
            "matched_skills": skills_data["matched_skills"],
            "missing_skills": skills_data["missing_skills"],
        },
        "experience_details": experience_data,
        "formatting_details": formatting_data,
        "ai_analysis": ai_result,
    }

    return JSONResponse(content=result)


@app.post("/generate-report")
async def generate_report(analysis_result: dict):
    try:
        pdf_bytes = generate_pdf_report(analysis_result)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ats_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
