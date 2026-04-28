import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import AnalysisResponse
from services.parser import extract_text, clean_text
from services.nlp_extractor import extract_profile
from services.scorer import score_resume
from database import db

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    try:
        raw_text = extract_text(file_bytes, file.filename)
        clean = clean_text(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(clean) < 100:
        raise HTTPException(status_code=422, detail="Could not extract enough text from the file. Please ensure the resume has readable text.")

    profile = extract_profile(clean)
    resume_score = score_resume(profile)
    session_id = str(uuid.uuid4())

    record = {
        "session_id": session_id,
        "profile": profile.dict(),
        "resume_score": resume_score.dict(),
        "filename": file.filename,
    }
    await db.sessions.insert_one(record)

    return AnalysisResponse(
        session_id=session_id,
        profile=profile,
        resume_score=resume_score,
    )

@router.get("/session/{session_id}", response_model=AnalysisResponse)
async def get_session(session_id: str):
    doc = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return AnalysisResponse(**doc)
