import os
import json
from fastapi import APIRouter
from database import db

router = APIRouter()

METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "ml", "model_artifacts", "metrics.json")

@router.get("/model-metrics")
async def get_model_metrics():
    try:
        with open(METRICS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "message": "Model not trained yet. Run ml/train.py to train.",
            "accuracy": None,
            "f1_score": None,
        }

@router.get("/sessions/stats")
async def get_session_stats():
    total = await db.sessions.count_documents({})
    strong = await db.sessions.count_documents({"resume_score.label": "Strong"})
    average = await db.sessions.count_documents({"resume_score.label": "Average"})
    weak = await db.sessions.count_documents({"resume_score.label": "Weak"})

    pipeline = [{"$group": {"_id": None, "avg_score": {"$avg": "$resume_score.score"}}}]
    agg = await db.sessions.aggregate(pipeline).to_list(1)
    avg_score = round(agg[0]["avg_score"], 1) if agg else 0

    return {
        "total_sessions": total,
        "score_distribution": {"Strong": strong, "Average": average, "Weak": weak},
        "average_score": avg_score,
    }

@router.get("/recent")
async def get_recent_sessions(limit: int = 10):
    cursor = db.sessions.find(
        {},
        {"_id": 0, "session_id": 1, "profile.name": 1, "resume_score.score": 1,
         "resume_score.label": 1, "profile.skills": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit)
    return await cursor.to_list(limit)
