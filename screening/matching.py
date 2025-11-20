from typing import List, Dict
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
CHAT_MODEL = os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4o-mini')

def compute_match(resume_skills: List[str], jd_text: str, resume_text: str = '') -> Dict:
    """
    Use LLM to generate comprehensive match analysis with detailed insights.
    """
    prompt = f"""You are an expert recruiter analyzing a candidate's resume against a job description.

JOB DESCRIPTION:
{jd_text[:3000]}

RESUME:
{resume_text[:4000]}

Analyze the candidate and provide:
1. A match score (0-100) based on how well the candidate fits the job requirements
2. Key strengths (4-6 detailed points) explaining why they're a good fit. Each strength should be specific, cite actual experience, and explain the relevance.
3. Gaps or missing qualifications (2-4 points) that could be concerns
4. A comprehensive paragraph of "Key Insights" that:
   - Summarizes the candidate's overall fit
   - Highlights their strongest qualifications
   - Addresses any concerns or gaps
   - Provides a recommendation on next steps
   - Maintains a professional, balanced tone

Format each strength and gap as complete, detailed sentences (not just keywords).

Respond ONLY with valid JSON in this exact format:
{{
  "matchScore": 85,
  "strengths": [
    "Proven experience with LLM frameworks (LangChain, LangGraph) which aligns directly with the job's core responsibilities.",
    "Solid backend development experience using Django and FastAPI, essential for production-grade services."
  ],
  "gaps": [
    "Lacks explicit mention of experience with Docker, part of the job's required tools.",
    "No clear evidence of MLOps practices beyond AWS deployments."
  ],
  "insights": "The candidate presents a compelling profile with strong technical foundations... [detailed paragraph]"
}}"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError('Empty response from OpenAI')
        
        import json
        result = json.loads(content)
        
        # Ensure proper structure
        return {
            'match_score': result.get('matchScore', 50),
            'strengths': result.get('strengths', ['Unable to analyze strengths']),
            'gaps': result.get('gaps', ['Unable to analyze gaps']),
            'insights': result.get('insights', 'Analysis unavailable')
        }
    except Exception as e:
        print(f"Error in LLM analysis: {e}")
        # Fallback to basic analysis
        resume_set = set(resume_skills)
        jd_lower = jd_text.lower()
        jd_tokens = [t for t in jd_lower.split() if len(t) > 2]
        from collections import Counter
        jd_counts = Counter(jd_tokens)
        required = [w for w in jd_counts if w in resume_set]
        coverage_ratio = len(required) / max(len(set(jd_counts)), 1)
        score = round(min(1.0, coverage_ratio) * 100, 2)
        
        return {
            'match_score': score,
            'strengths': [f"Experience with {s}" for s in required[:5]],
            'gaps': [f"No clear mention of {g}" for g in list(set(jd_counts.keys()) - resume_set)[:3]],
            'insights': f"The candidate shows {coverage_ratio*100:.0f}% alignment with job requirements based on keyword analysis."
        }
