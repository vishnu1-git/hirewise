from fastapi import APIRouter, HTTPException
from models.schemas import CompareRequest, CompareResponse, RoleRanking
from services.match_service import compute_match
from database import db

router = APIRouter()

@router.post("/", response_model=CompareResponse)
async def compare_roles(req: CompareRequest):
    if len(req.job_descriptions) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 job descriptions to compare.")
    if len(req.job_descriptions) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 roles can be compared at once.")

    doc = await db.sessions.find_one({"session_id": req.session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found.")

    from models.schemas import ExtractedProfile
    profile = ExtractedProfile(**doc["profile"])

    rankings = []
    for jd_entry in req.job_descriptions:
        title = jd_entry.get("title", "Unknown Role")
        jd_text = jd_entry.get("description", "")
        if not jd_text.strip():
            continue
        match_result, recommendation = await compute_match(profile, jd_text)
        rankings.append({
            "job_title": title,
            "match_score": match_result.match_score,
            "match_result": match_result,
            "recommendation": recommendation,
        })

    # Sort by match score descending
    rankings.sort(key=lambda x: x["match_score"], reverse=True)

    ranked = [
        RoleRanking(
            rank=i + 1,
            job_title=r["job_title"],
            match_score=r["match_score"],
            match_result=r["match_result"],
            recommendation=r["recommendation"],
        )
        for i, r in enumerate(rankings)
    ]

    best_fit = ranked[0].job_title if ranked else "None"
    gap = ranked[0].match_score - ranked[-1].match_score if len(ranked) > 1 else 0

    summary = (
        f"Best fit: {best_fit} ({ranked[0].match_score:.0f}% match). "
        f"Compared {len(ranked)} roles with a {gap:.0f}pt spread. "
        f"Focus on {best_fit} while building skills for other roles."
    )

    await db.sessions.update_one(
        {"session_id": req.session_id},
        {"$set": {"compare_result": [r.dict() for r in ranked]}}
    )

    return CompareResponse(
        session_id=req.session_id,
        rankings=ranked,
        best_fit=best_fit,
        analysis_summary=summary,
    )
