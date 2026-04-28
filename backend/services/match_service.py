import re
from typing import List, Set, Tuple
from models.schemas import ExtractedProfile, MatchResult
from services.embedder import compute_resume_jd_similarity
from services.nlp_extractor import extract_skills, SKILLS_DB


ALL_SKILLS_SET = set()
for cat_skills in SKILLS_DB.values():
    ALL_SKILLS_SET.update(cat_skills)


def extract_jd_requirements(jd_text: str) -> dict:
    """Extract structured requirements from job description."""
    skills = extract_skills(jd_text)

    # Extract years of experience required
    exp_pattern = r'(\d+)\+?\s*years?\s+(?:of\s+)?experience'
    exp_matches = re.findall(exp_pattern, jd_text.lower())
    required_exp = float(exp_matches[0]) if exp_matches else 0.0

    # Extract education requirements
    edu_required = "Any"
    jd_lower = jd_text.lower()
    if "phd" in jd_lower or "doctorate" in jd_lower:
        edu_required = "PhD"
    elif "master" in jd_lower or "m.tech" in jd_lower:
        edu_required = "Masters"
    elif "bachelor" in jd_lower or "b.tech" in jd_lower or "degree" in jd_lower:
        edu_required = "Bachelors"

    return {
        "required_skills": skills,
        "required_exp": required_exp,
        "education": edu_required
    }


def compute_skill_overlap(
    resume_skills: List[str],
    jd_skills: List[str]
) -> Tuple[List[str], List[str], List[str], float]:
    """Compute matched, missing, extra skills and keyword overlap ratio."""
    resume_set = {s.lower() for s in resume_skills}
    jd_set = {s.lower() for s in jd_skills}

    matched = list(resume_set & jd_set)
    missing = list(jd_set - resume_set)
    extra = list(resume_set - jd_set)

    overlap = len(matched) / max(len(jd_set), 1)

    # Restore proper casing
    resume_dict = {s.lower(): s for s in resume_skills}
    jd_dict = {s.lower(): s for s in jd_skills}

    matched_display = [jd_dict.get(s, resume_dict.get(s, s.title())) for s in matched]
    missing_display = [jd_dict.get(s, s.title()) for s in missing]
    extra_display = [resume_dict.get(s, s.title()) for s in extra]

    return matched_display, missing_display, extra_display, round(overlap, 4)


def _score_to_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"


def _generate_recommendation(match_result: MatchResult, profile: ExtractedProfile) -> str:
    score = match_result.match_score
    missing = match_result.missing_skills[:3]

    if score >= 80:
        return (
            f"Excellent fit! You match {score:.0f}% of the job requirements. "
            "Apply with confidence — consider tailoring your resume to highlight your top relevant projects."
        )
    elif score >= 65:
        missing_str = ', '.join(missing) if missing else "a few areas"
        return (
            f"Good match at {score:.0f}%. Bridge the gap by acquiring skills in: {missing_str}. "
            "You're competitive for this role."
        )
    elif score >= 45:
        missing_str = ', '.join(missing) if missing else "several key areas"
        return (
            f"Fair match at {score:.0f}%. You're missing key skills: {missing_str}. "
            "Focus on 1-2 critical skills before applying, or target similar roles where you score higher."
        )
    else:
        return (
            f"Low match at {score:.0f}%. This role requires significant skill development. "
            f"Priority skills to acquire: {', '.join(missing[:4])}. Consider similar entry-level roles."
        )


async def compute_match(profile: ExtractedProfile, job_description: str) -> Tuple[MatchResult, str]:
    """Full resume-JD matching pipeline."""
    # 1. Extract JD requirements
    jd_requirements = extract_jd_requirements(job_description)

    # 2. Semantic similarity via embeddings
    semantic_sim = compute_resume_jd_similarity(profile.raw_text, job_description)

    # 3. Skill overlap analysis
    matched_skills, missing_skills, extra_skills, keyword_overlap = compute_skill_overlap(
        profile.skills, jd_requirements["required_skills"]
    )

    # 4. Composite match score
    # Semantic (40%) + skill overlap (40%) + experience (20%)
    exp_score = 1.0
    if jd_requirements["required_exp"] > 0:
        exp_score = min(profile.experience_years / jd_requirements["required_exp"], 1.0)

    match_score = (
        semantic_sim * 40 +
        keyword_overlap * 40 +
        exp_score * 20
    )
    match_score = round(min(max(match_score, 0), 100), 1)

    role_fit_label = _score_to_label(match_score)

    match_result = MatchResult(
        match_score=match_score,
        matched_skills=matched_skills[:20],
        missing_skills=missing_skills[:20],
        extra_skills=extra_skills[:10],
        semantic_similarity=round(semantic_sim * 100, 1),
        keyword_overlap=round(keyword_overlap * 100, 1),
        role_fit_label=role_fit_label
    )

    recommendation = _generate_recommendation(match_result, profile)
    return match_result, recommendation
