from fastapi import APIRouter, HTTPException
from models.schemas import (
    QuestionRequest, QuestionsResponse,
    AnswerSubmission, AnswerEvaluation
)
from services.question_gen import generate_questions
from services.answer_eval import evaluate_answer
from database import db

router = APIRouter()

@router.post("/questions", response_model=QuestionsResponse)
async def get_interview_questions(req: QuestionRequest):
    doc = await db.sessions.find_one({"session_id": req.session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found.")

    from models.schemas import ExtractedProfile
    profile = ExtractedProfile(**doc["profile"])

    questions = await generate_questions(
        profile=profile,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
        focus_areas=req.focus_areas,
    )

    # Persist questions to session
    await db.sessions.update_one(
        {"session_id": req.session_id},
        {"$set": {"questions": [q.dict() for q in questions]}}
    )

    return QuestionsResponse(
        session_id=req.session_id,
        questions=questions,
        total=len(questions),
    )

@router.post("/evaluate", response_model=AnswerEvaluation)
async def evaluate_interview_answer(submission: AnswerSubmission):
    evaluation = await evaluate_answer(submission)

    # Store result in DB
    await db.sessions.update_one(
        {"session_id": submission.session_id},
        {"$push": {"evaluations": evaluation.dict()}}
    )
    return evaluation

@router.get("/history/{session_id}")
async def get_interview_history(session_id: str):
    doc = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "session_id": session_id,
        "questions": doc.get("questions", []),
        "evaluations": doc.get("evaluations", []),
    }
