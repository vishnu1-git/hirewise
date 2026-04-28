from typing import List, Dict
from models.schemas import AnswerSubmission, AnswerEvaluation
from services.embedder import compute_answer_similarity
from services.question_gen import generate_ideal_answer
import re


def _extract_concepts_from_answer(answer: str) -> List[str]:
    """Extract key technical concepts mentioned in an answer."""
    concept_indicators = [
        "algorithm", "complexity", "pattern", "architecture", "database",
        "cache", "queue", "api", "framework", "library", "model", "layer",
        "hash", "tree", "graph", "array", "pointer", "async", "thread",
        "process", "memory", "network", "protocol", "encryption"
    ]
    answer_lower = answer.lower()
    found = []
    for concept in concept_indicators:
        if concept in answer_lower:
            found.append(concept)
    return found


def _check_concept_coverage(
    answer: str,
    expected_concepts: List[str]
) -> Dict[str, List[str]]:
    """Check which expected concepts are covered in the answer."""
    answer_lower = answer.lower()
    matched = []
    missing = []
    for concept in expected_concepts:
        # Check if concept or close variant appears in answer
        concept_words = concept.lower().split()
        # All words of concept should appear
        if all(word in answer_lower for word in concept_words):
            matched.append(concept)
        elif any(word in answer_lower for word in concept_words if len(word) > 3):
            matched.append(concept)  # Partial match counts
        else:
            missing.append(concept)
    return {"matched": matched, "missing": missing}


def _compute_structural_score(answer: str) -> float:
    """Score answer structure: length, clarity, examples."""
    score = 0.0
    word_count = len(answer.split())

    # Length scoring (ideal: 100-300 words)
    if word_count >= 50:
        score += 1.5
    if word_count >= 100:
        score += 1.0
    if word_count >= 200:
        score += 0.5
    if word_count > 500:
        score -= 1.0  # Too verbose

    # Examples mentioned
    if re.search(r'\bfor example\b|\bfor instance\b|\bsuch as\b|\be\.g\b', answer.lower()):
        score += 1.0

    # Structure indicators
    if re.search(r'\bfirst(ly)?\b|\bsecond(ly)?\b|\bthird(ly)?\b|\bfinally\b', answer.lower()):
        score += 0.5

    # Quantified claims
    if re.search(r'\d+%|\d+ times|\d+ seconds|\d+ms|O\(', answer):
        score += 1.0

    return min(score, 4.0)


def _generate_strengths(
    answer: str,
    similarity: float,
    matched_concepts: List[str],
    structural_score: float
) -> List[str]:
    strengths = []
    if similarity >= 0.7:
        strengths.append("Answer demonstrates strong understanding of the topic.")
    if len(matched_concepts) >= 3:
        strengths.append(f"Covered key concepts: {', '.join(matched_concepts[:3])}.")
    if structural_score >= 3.0:
        strengths.append("Well-structured response with clear examples.")
    if len(answer.split()) >= 150:
        strengths.append("Comprehensive answer with sufficient depth.")
    return strengths or ["Answer provided — needs more technical depth."]


def _generate_improvements(
    missing_concepts: List[str],
    similarity: float,
    structural_score: float,
    word_count: int
) -> List[str]:
    improvements = []
    if missing_concepts:
        improvements.append(f"Missing key concepts: {', '.join(missing_concepts[:3])}. Include these in your answer.")
    if similarity < 0.5:
        improvements.append("Answer drifts from the core topic. Re-read the question and focus your response.")
    if structural_score < 2.0:
        improvements.append("Improve structure: use 'First... Second... Finally...' format for clarity.")
    if word_count < 50:
        improvements.append("Answer is too brief. Provide more detail and examples.")
    if word_count > 450:
        improvements.append("Answer is too long. Be more concise and focused.")
    return improvements or ["Great answer overall! Consider adding more real-world examples."]


async def evaluate_answer(submission: AnswerSubmission) -> AnswerEvaluation:
    """Full answer evaluation pipeline."""
    answer = submission.user_answer.strip()

    if not answer or len(answer) < 10:
        return AnswerEvaluation(
            question_id=submission.question_id,
            score=0.0,
            grade="Poor",
            similarity_score=0.0,
            matched_concepts=[],
            missing_concepts=submission.expected_concepts,
            strengths=["No answer provided."],
            improvements=["Please provide a detailed answer."],
            detailed_feedback="No answer was submitted. Please attempt to answer every question."
        )

    # 1. Generate ideal answer for comparison
    ideal_answer = await generate_ideal_answer(
        submission.question_text,
        submission.expected_concepts
    )

    # 2. Semantic similarity (0–1)
    similarity = compute_answer_similarity(answer, ideal_answer)

    # 3. Concept coverage
    coverage = _check_concept_coverage(answer, submission.expected_concepts)
    matched = coverage["matched"]
    missing = coverage["missing"]

    # 4. Structure score (0–4)
    structural_score = _compute_structural_score(answer)

    # 5. Compute final score (0–10)
    concept_ratio = len(matched) / max(len(submission.expected_concepts), 1)
    
    score = (
        similarity * 4.0 +           # Semantic closeness (40%)
        concept_ratio * 3.0 +         # Concept coverage (30%)
        structural_score * 0.75 +     # Structure (22.5%)
        0.75                          # Attempt bonus (7.5%)
    )
    score = round(min(max(score, 0), 10), 1)

    # 6. Grade
    if score >= 8.5:
        grade = "Excellent"
    elif score >= 7.0:
        grade = "Good"
    elif score >= 5.0:
        grade = "Average"
    else:
        grade = "Poor"

    # 7. Generate feedback
    word_count = len(answer.split())
    strengths = _generate_strengths(answer, similarity, matched, structural_score)
    improvements = _generate_improvements(missing, similarity, structural_score, word_count)

    # 8. Detailed feedback
    detailed_feedback = (
        f"Score: {score}/10 ({grade}). "
        f"Your answer covered {len(matched)}/{len(submission.expected_concepts)} key concepts. "
        f"Semantic alignment with ideal answer: {similarity*100:.0f}%. "
    )
    if missing:
        detailed_feedback += f"Key missing areas: {', '.join(missing[:3])}. "
    if score >= 7:
        detailed_feedback += "Strong response — you clearly understand this topic."
    else:
        detailed_feedback += "Keep practicing — review the missing concepts and try again."

    return AnswerEvaluation(
        question_id=submission.question_id,
        score=score,
        grade=grade,
        similarity_score=round(similarity, 3),
        matched_concepts=matched,
        missing_concepts=missing,
        strengths=strengths,
        improvements=improvements,
        detailed_feedback=detailed_feedback
    )
