from fastapi import APIRouter, HTTPException
from models.schemas import MatchRequest, MatchResponse
from services.match_service import compute_match
from database import db

router = APIRouter()

@router.post("/", response_model=MatchResponse)
async def match_resume_to_jd(req: MatchRequest):
    doc = await db.sessions.find_one({"session_id": req.session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a resume first.")

    from models.schemas import ExtractedProfile
    profile = ExtractedProfile(**doc["profile"])
    match_result, recommendation = await compute_match(profile, req.job_description)

    overall_score = round(
        match_result.match_score * 0.6 + doc["resume_score"]["score"] * 0.4, 1
    )

    result_doc = {
        "job_title": req.job_title,
        "match_result": match_result.dict(),
        "overall_score": overall_score,
        "recommendation": recommendation,
    }
    await db.sessions.update_one(
        {"session_id": req.session_id},
        {"$set": {"last_match": result_doc}}
    )

    return MatchResponse(
        session_id=req.session_id,
        job_title=req.job_title,
        match_result=match_result,
        overall_score=overall_score,
        recommendation=recommendation,
    )
