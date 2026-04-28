from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExtractedProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: float = 0.0
    education_level: str = "Unknown"
    education_field: Optional[str] = None
    projects: List[str] = []
    project_complexity_score: float = 0.0
    certifications: List[str] = []
    raw_text: str = ""


class SHAPExplanation(BaseModel):
    feature: str
    value: float
    impact: float
    direction: str  # "positive" | "negative"


class ResumeScore(BaseModel):
    score: float = Field(..., ge=0, le=100)
    label: str  # "Strong" | "Average" | "Weak"
    confidence: float
    shap_explanations: List[SHAPExplanation] = []
    feature_values: Dict[str, Any] = {}
    feedback: List[str] = []


class MatchResult(BaseModel):
    match_score: float = Field(..., ge=0, le=100)
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    extra_skills: List[str] = []
    semantic_similarity: float
    keyword_overlap: float
    role_fit_label: str  # "Excellent" | "Good" | "Fair" | "Poor"


class AnalysisResponse(BaseModel):
    session_id: str
    profile: ExtractedProfile
    resume_score: ResumeScore
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MatchRequest(BaseModel):
    session_id: str
    job_description: str
    job_title: Optional[str] = None


class MatchResponse(BaseModel):
    session_id: str
    job_title: Optional[str] = None
    match_result: MatchResult
    overall_score: float
    recommendation: str


class QuestionRequest(BaseModel):
    session_id: str
    num_questions: int = Field(default=5, ge=1, le=15)
    difficulty: str = Field(default="medium")  # easy | medium | hard
    focus_areas: Optional[List[str]] = None


class Question(BaseModel):
    id: str
    question: str
    category: str  # "technical" | "behavioral" | "system_design" | "project"
    difficulty: str
    expected_concepts: List[str] = []
    ideal_answer_hint: Optional[str] = None


class QuestionsResponse(BaseModel):
    session_id: str
    questions: List[Question]
    total: int


class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    question_text: str
    user_answer: str
    expected_concepts: List[str] = []


class AnswerEvaluation(BaseModel):
    question_id: str
    score: float = Field(..., ge=0, le=10)
    grade: str  # "Excellent" | "Good" | "Average" | "Poor"
    similarity_score: float
    matched_concepts: List[str] = []
    missing_concepts: List[str] = []
    strengths: List[str] = []
    improvements: List[str] = []
    detailed_feedback: str


class CompareRequest(BaseModel):
    session_id: str
    job_descriptions: List[Dict[str, str]]  # [{"title": "...", "description": "..."}]


class RoleRanking(BaseModel):
    rank: int
    job_title: str
    match_score: float
    match_result: MatchResult
    recommendation: str


class CompareResponse(BaseModel):
    session_id: str
    rankings: List[RoleRanking]
    best_fit: str
    analysis_summary: str


class ModelMetrics(BaseModel):
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    cv_scores: List[float]
    confusion_matrix: List[List[int]]
    feature_importances: Dict[str, float]
    model_name: str
    training_samples: int
