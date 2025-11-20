from typing import List, Dict
from collections import Counter
import math

def compute_match(resume_skills: List[str], jd_text: str) -> Dict:
    jd_lower = jd_text.lower()
    jd_tokens = [t for t in jd_lower.split() if len(t) > 2]
    jd_counts = Counter(jd_tokens)

    resume_set = set(resume_skills)

    required = [w for w in jd_counts if w in resume_set]
    coverage_ratio = len(required) / max(len(set(jd_counts)), 1)
    score = round(min(1.0, coverage_ratio) * 100, 2)

    strengths = required[:15]
    gaps = [w for w in jd_counts if w not in resume_set][:15]

    insights = {
        'resume_skill_count': len(resume_skills),
        'jd_token_count': len(jd_counts),
        'coverage_ratio': coverage_ratio
    }
    return {
        'match_score': score,
        'strengths': strengths,
        'gaps': gaps,
        'insights': insights
    }
