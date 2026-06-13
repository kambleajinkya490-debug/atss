import anthropic
import json
import os


def analyze_with_claude(
    resume_text: str,
    jd_text: str,
    score_data: dict,
    api_key: str
) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyst and career coach.

Analyze this resume against the job description and provide detailed, actionable feedback.

=== JOB DESCRIPTION ===
{jd_text[:3000]}

=== RESUME ===
{resume_text[:3000]}

=== PRELIMINARY SCORES ===
- Keyword Match: {score_data.get('keyword_score', 0):.0%}
- Skills Match: {score_data.get('skills_score', 0):.0%}
- Experience: {score_data.get('experience_score', 0):.0%}
- Education: {score_data.get('education_score', 0):.0%}
- Formatting: {score_data.get('formatting_score', 0):.0%}

Respond ONLY with a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "overall_assessment": "2-3 sentence professional assessment",
  "top_suggestions": [
    {{
      "priority": "High",
      "title": "Short title",
      "description": "Specific actionable advice"
    }},
    {{
      "priority": "High",
      "title": "Short title",
      "description": "Specific actionable advice"
    }},
    {{
      "priority": "Medium",
      "title": "Short title",
      "description": "Specific actionable advice"
    }},
    {{
      "priority": "Medium",
      "title": "Short title",
      "description": "Specific actionable advice"
    }},
    {{
      "priority": "Low",
      "title": "Short title",
      "description": "Specific actionable advice"
    }}
  ],
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "critical_gaps": ["gap 1", "gap 2", "gap 3"],
  "score_adjustments": {{
    "keyword_adjustment": 0,
    "skills_adjustment": 0,
    "experience_adjustment": 0
  }}
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        # Strip markdown fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text)
        return result

    except json.JSONDecodeError:
        return {
            "overall_assessment": "Analysis completed. Review the detailed scores below.",
            "top_suggestions": [
                {
                    "priority": "High",
                    "title": "Add Missing Keywords",
                    "description": "Incorporate the missing keywords from the job description naturally into your resume."
                },
                {
                    "priority": "High",
                    "title": "Quantify Achievements",
                    "description": "Add specific numbers and metrics to demonstrate the impact of your work."
                },
                {
                    "priority": "Medium",
                    "title": "Tailor Your Summary",
                    "description": "Rewrite your professional summary to mirror the job description's language."
                },
                {
                    "priority": "Medium",
                    "title": "Skills Section",
                    "description": "Ensure your skills section lists all required technologies from the job posting."
                },
                {
                    "priority": "Low",
                    "title": "Formatting Consistency",
                    "description": "Use consistent formatting throughout your resume for better ATS parsing."
                }
            ],
            "strengths": ["Relevant work history", "Technical skills present", "Education included"],
            "critical_gaps": ["Some required keywords missing", "Quantified achievements needed"],
            "score_adjustments": {"keyword_adjustment": 0, "skills_adjustment": 0, "experience_adjustment": 0}
        }
    except Exception as e:
        raise RuntimeError(f"Claude API error: {str(e)}")
