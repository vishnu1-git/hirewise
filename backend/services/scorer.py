import os
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional
from models.schemas import ExtractedProfile, ResumeScore, SHAPExplanation

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "model_artifacts")
BEST_MODEL_FILE = os.path.join(MODEL_PATH, "best_model.pkl")
SCALER_FILE = os.path.join(MODEL_PATH, "scaler.pkl")
LABEL_ENCODER_FILE = os.path.join(MODEL_PATH, "label_encoder.pkl")

_model = None
_scaler = None
_label_encoder = None

FEATURE_NAMES = [
    "skills_count",
    "relevant_skills_count",
    "experience_years",
    "project_complexity_score",
    "education_score",
    "has_ml_skills",
    "has_cloud_skills",
    "has_web_skills",
    "certifications_count",
    "text_length_score",
]

EDUCATION_SCORE_MAP = {
    "PhD": 5, "Masters": 4, "Bachelors": 3,
    "Diploma": 2, "High School": 1, "Unknown": 0
}

ML_SKILLS = {"python", "machine learning", "deep learning", "tensorflow", "pytorch",
             "scikit-learn", "nlp", "data science", "xgboost", "transformers", "keras"}
CLOUD_SKILLS = {"aws", "gcp", "azure", "docker", "kubernetes", "ci/cd", "terraform"}
WEB_SKILLS = {"react", "node.js", "django", "fastapi", "flask", "angular", "vue",
              "javascript", "typescript"}


def _load_models():
    global _model, _scaler, _label_encoder
    if _model is None:
        try:
            with open(BEST_MODEL_FILE, "rb") as f:
                _model = pickle.load(f)
            with open(SCALER_FILE, "rb") as f:
                _scaler = pickle.load(f)
            with open(LABEL_ENCODER_FILE, "rb") as f:
                _label_encoder = pickle.load(f)
            print("[Scorer] Models loaded from disk.")
        except FileNotFoundError:
            print("[Scorer] Model files not found. Run ml/train.py first.")
            _model = None


def extract_features(profile: ExtractedProfile) -> np.ndarray:
    """Convert extracted profile to ML feature vector."""
    skills_lower = {s.lower() for s in profile.skills}
    
    features = {
        "skills_count": min(len(profile.skills) / 20.0, 1.0),
        "relevant_skills_count": min(len(profile.skills) / 15.0, 1.0),
        "experience_years": min(profile.experience_years / 10.0, 1.0),
        "project_complexity_score": profile.project_complexity_score / 10.0,
        "education_score": EDUCATION_SCORE_MAP.get(profile.education_level, 0) / 5.0,
        "has_ml_skills": float(bool(skills_lower & ML_SKILLS)),
        "has_cloud_skills": float(bool(skills_lower & CLOUD_SKILLS)),
        "has_web_skills": float(bool(skills_lower & WEB_SKILLS)),
        "certifications_count": min(len(profile.certifications) / 5.0, 1.0),
        "text_length_score": min(len(profile.raw_text) / 3000.0, 1.0),
    }

    return np.array([features[name] for name in FEATURE_NAMES])


def _rule_based_score(profile: ExtractedProfile) -> Tuple[float, str, List[str]]:
    """Fallback rule-based scoring when ML model not available."""
    score = 0.0
    feedback = []

    # Skills contribution (0–30 pts)
    skill_score = min(len(profile.skills) * 2, 30)
    score += skill_score
    if len(profile.skills) < 5:
        feedback.append("Add more technical skills to your resume.")

    # Experience (0–25 pts)
    exp_score = min(profile.experience_years * 5, 25)
    score += exp_score
    if profile.experience_years == 0:
        feedback.append("Add internship/work experience or specify duration.")

    # Education (0–20 pts)
    edu_score = EDUCATION_SCORE_MAP.get(profile.education_level, 0) * 4
    score += edu_score

    # Project complexity (0–15 pts)
    proj_score = profile.project_complexity_score * 1.5
    score += proj_score
    if profile.project_complexity_score < 3:
        feedback.append("Showcase more complex, impactful projects.")

    # Diversity bonus (0–10 pts)
    skills_lower = {s.lower() for s in profile.skills}
    diversity = sum([
        bool(skills_lower & ML_SKILLS),
        bool(skills_lower & CLOUD_SKILLS),
        bool(skills_lower & WEB_SKILLS),
    ]) * 3.33
    score += diversity

    score = round(min(max(score, 0), 100), 1)
    label = "Strong" if score >= 70 else ("Average" if score >= 45 else "Weak")
    return score, label, feedback


def _generate_shap_explanations(
    features: np.ndarray,
    model,
    score: float
) -> List[SHAPExplanation]:
    """Generate SHAP-style explanations (real SHAP if available, else approximation)."""
    explanations = []

    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(features.reshape(1, -1))
        # For multi-class, pick the predicted class
        if isinstance(shap_vals, list):
            label_idx = int(np.argmax(model.predict_proba(features.reshape(1, -1))[0]))
            vals = shap_vals[label_idx][0]
        else:
            vals = shap_vals[0]

        for i, (name, val) in enumerate(zip(FEATURE_NAMES, vals)):
            if abs(val) > 0.001:
                explanations.append(SHAPExplanation(
                    feature=name.replace("_", " ").title(),
                    value=round(float(features[i]), 3),
                    impact=round(float(val), 4),
                    direction="positive" if val > 0 else "negative"
                ))
        explanations.sort(key=lambda x: abs(x.impact), reverse=True)

    except (ImportError, Exception):
        # Fallback: use feature importances
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        else:
            importances = np.ones(len(FEATURE_NAMES)) / len(FEATURE_NAMES)

        for i, (name, feat_val) in enumerate(zip(FEATURE_NAMES, features)):
            impact = float(importances[i]) * (1 if feat_val > 0.3 else -0.5)
            explanations.append(SHAPExplanation(
                feature=name.replace("_", " ").title(),
                value=round(float(feat_val), 3),
                impact=round(impact, 4),
                direction="positive" if impact > 0 else "negative"
            ))
        explanations.sort(key=lambda x: abs(x.impact), reverse=True)

    return explanations[:8]


def _generate_feedback(
    profile: ExtractedProfile,
    features: np.ndarray,
    shap_explanations: List[SHAPExplanation]
) -> List[str]:
    """Generate actionable feedback based on score drivers."""
    feedback = []
    skills_lower = {s.lower() for s in profile.skills}

    if profile.experience_years < 1:
        feedback.append("No work experience detected. Add internships, part-time roles, or freelance projects.")
    elif profile.experience_years < 2:
        feedback.append(f"You have {profile.experience_years:.1f} years of experience. Consider adding more to strengthen your profile.")

    if len(profile.skills) < 8:
        feedback.append("Resume lists fewer than 8 skills. Expand your technical skill section with tools you actually use.")

    if profile.project_complexity_score < 4:
        feedback.append("Projects appear basic. Describe impact, scale, and technologies used for each project.")

    if not (skills_lower & ML_SKILLS) and not (skills_lower & WEB_SKILLS):
        feedback.append("No domain-specific skills detected. Highlight specialization in ML/AI, web, cloud, or data engineering.")

    if not (skills_lower & CLOUD_SKILLS):
        feedback.append("No cloud or DevOps skills found. Even basic Docker/AWS knowledge significantly boosts your score.")

    if profile.education_level in ["Unknown", "High School"]:
        feedback.append("Education details unclear. Explicitly state your degree, institution, and graduation year.")

    if len(profile.projects) == 0:
        feedback.append("No projects section detected. Add 2-3 substantial projects with tech stack and outcomes.")

    # Positive feedback
    if profile.experience_years >= 3:
        feedback.append(f"✓ Strong experience: {profile.experience_years:.1f} years is a competitive profile.")
    if len(profile.skills) >= 15:
        feedback.append(f"✓ Excellent skill breadth: {len(profile.skills)} skills detected across multiple domains.")

    return feedback


def score_resume(profile: ExtractedProfile, semantic_match: float = 0.5) -> ResumeScore:
    """Main entry point: score a resume and return full explanation."""
    _load_models()
    features = extract_features(profile)

    if _model is None:
        # Rule-based fallback
        score, label, feedback = _rule_based_score(profile)
        return ResumeScore(
            score=score,
            label=label,
            confidence=0.75,
            shap_explanations=[],
            feature_values={FEATURE_NAMES[i]: round(float(features[i]), 3)
                            for i in range(len(FEATURE_NAMES))},
            feedback=feedback
        )

    # ML scoring
    if _scaler:
        X = _scaler.transform(features.reshape(1, -1))
    else:
        X = features.reshape(1, -1)

    proba = _model.predict_proba(X)[0]
    pred_class = int(np.argmax(proba))
    confidence = float(np.max(proba))

    if _label_encoder:
        label = _label_encoder.inverse_transform([pred_class])[0]
    else:
        label_map = {0: "Weak", 1: "Average", 2: "Strong"}
        label = label_map.get(pred_class, "Average")

    # Convert probability to 0-100 score
    # Strong=2, Average=1, Weak=0 → weighted score
    proba_dict = {_label_encoder.inverse_transform([i])[0] if _label_encoder else ["Weak","Average","Strong"][i]: p
                  for i, p in enumerate(proba)}
    
    score = (
        proba_dict.get("Strong", proba[2]) * 100 * 0.85 +
        proba_dict.get("Average", proba[1]) * 60 * 0.10 +
        proba_dict.get("Weak", proba[0]) * 20 * 0.05
    )
    # Add semantic match bonus
    score = score * 0.85 + semantic_match * 100 * 0.15
    score = round(min(max(score, 5), 98), 1)

    shap_explanations = _generate_shap_explanations(features, _model, score)
    feedback = _generate_feedback(profile, features, shap_explanations)

    return ResumeScore(
        score=score,
        label=label,
        confidence=round(confidence, 3),
        shap_explanations=shap_explanations,
        feature_values={FEATURE_NAMES[i]: round(float(features[i]), 3)
                        for i in range(len(FEATURE_NAMES))},
        feedback=feedback
    )
