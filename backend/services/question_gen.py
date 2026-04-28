import os
import json
import uuid
import httpx
from typing import List, Optional
from models.schemas import ExtractedProfile, Question

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"


async def generate_questions(
    profile: ExtractedProfile,
    num_questions: int = 5,
    difficulty: str = "medium",
    focus_areas: Optional[List[str]] = None
) -> List[Question]:
    """Generate personalized interview questions using Claude API."""

    skills_str = ", ".join(profile.skills[:15]) if profile.skills else "General programming"
    projects_str = "; ".join(profile.projects[:3]) if profile.projects else "None specified"
    focus_str = ", ".join(focus_areas) if focus_areas else "all areas"

    prompt = f"""You are an expert technical interviewer at a top tech company.

Candidate Profile:
- Skills: {skills_str}
- Experience: {profile.experience_years:.1f} years
- Education: {profile.education_level}
- Recent Projects: {projects_str}
- Focus areas requested: {focus_str}

Generate exactly {num_questions} interview questions tailored to this specific candidate's background.
Difficulty: {difficulty}

Rules:
1. Mix question types: technical (40%), behavioral (25%), system design (20%), project-based (15%)
2. Reference their actual skills and projects where relevant
3. Scale complexity to their experience level
4. For each question, include expected concepts the ideal answer should cover

Return ONLY a JSON array with this exact structure (no markdown, no preamble):
[
  {{
    "question": "...",
    "category": "technical|behavioral|system_design|project",
    "difficulty": "easy|medium|hard",
    "expected_concepts": ["concept1", "concept2"],
    "ideal_answer_hint": "Brief hint for evaluator only"
  }}
]"""

    if not ANTHROPIC_API_KEY:
        return _fallback_questions(profile, num_questions, difficulty)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            data = response.json()
            text = data["content"][0]["text"].strip()

            # Clean JSON
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            questions_data = json.loads(text)
            questions = []
            for i, q in enumerate(questions_data):
                questions.append(Question(
                    id=str(uuid.uuid4()),
                    question=q.get("question", ""),
                    category=q.get("category", "technical"),
                    difficulty=q.get("difficulty", difficulty),
                    expected_concepts=q.get("expected_concepts", []),
                    ideal_answer_hint=q.get("ideal_answer_hint")
                ))
            return questions

    except Exception as e:
        print(f"[QuestionGen] Claude API error: {e}. Using fallback.")
        return _fallback_questions(profile, num_questions, difficulty)


async def generate_ideal_answer(question: str, expected_concepts: List[str]) -> str:
    """Generate an ideal answer for comparison during evaluation."""
    if not ANTHROPIC_API_KEY:
        return " ".join(expected_concepts)

    prompt = f"""Provide a concise, ideal interview answer for the following question.
Cover these concepts: {', '.join(expected_concepts)}

Question: {question}

Provide a clear, structured answer in 150-250 words. This is the reference answer for evaluation."""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            data = response.json()
            return data["content"][0]["text"].strip()
    except Exception:
        return " ".join(expected_concepts)


def _fallback_questions(
    profile: ExtractedProfile,
    num_questions: int,
    difficulty: str
) -> List[Question]:
    """Rule-based question generation when API not available."""
    questions = []
    skills = profile.skills[:5] if profile.skills else ["Python"]
    projects = profile.projects[:2] if profile.projects else []

    templates = [
        # Technical
        {
            "question": f"Explain how you would optimize a {skills[0]} application for performance at scale.",
            "category": "technical",
            "expected_concepts": ["profiling", "caching", "async", "database optimization", "load balancing"],
            "ideal_answer_hint": "Cover profiling, bottlenecks, caching strategies, async patterns"
        },
        {
            "question": f"What are the key differences between supervised and unsupervised learning? Give examples from your work.",
            "category": "technical",
            "expected_concepts": ["labeled data", "clustering", "classification", "real examples"],
            "ideal_answer_hint": "Should mention regression, classification, k-means, dimensionality reduction"
        },
        {
            "question": f"How does {skills[0]} handle memory management?",
            "category": "technical",
            "expected_concepts": ["garbage collection", "heap", "stack", "memory leaks", "optimization"],
            "ideal_answer_hint": "Cover garbage collection, reference counting, memory profiling"
        },
        # Behavioral
        {
            "question": "Describe a time when you had to debug a complex issue under tight deadlines. How did you approach it?",
            "category": "behavioral",
            "expected_concepts": ["systematic approach", "root cause analysis", "communication", "prioritization"],
            "ideal_answer_hint": "STAR format: Situation, Task, Action, Result with quantifiable outcome"
        },
        {
            "question": "Tell me about a project where you had to learn a new technology quickly. What was your learning strategy?",
            "category": "behavioral",
            "expected_concepts": ["self-learning", "documentation", "community resources", "hands-on practice"],
            "ideal_answer_hint": "Look for structured learning approach, outcome, and application"
        },
        # System Design
        {
            "question": "Design a URL shortening service like bit.ly. What components would you need?",
            "category": "system_design",
            "expected_concepts": ["hash function", "database", "caching", "load balancer", "analytics", "scalability"],
            "ideal_answer_hint": "Hash generation, collision handling, read-heavy caching, horizontal scaling"
        },
        {
            "question": "How would you design a real-time notification system for 1 million users?",
            "category": "system_design",
            "expected_concepts": ["websockets", "message queues", "push notifications", "kafka", "scalability"],
            "ideal_answer_hint": "WebSockets for real-time, message queue for reliability, push for mobile"
        },
    ]

    if projects:
        templates.append({
            "question": f"Walk me through your project: '{projects[0]}'. What was the biggest technical challenge?",
            "category": "project",
            "expected_concepts": ["architecture", "challenges", "solutions", "impact", "learnings"],
            "ideal_answer_hint": "Look for clear problem statement, technical depth, measurable impact"
        })

    import random
    selected = templates[:num_questions] if len(templates) >= num_questions else templates
    if len(selected) < num_questions:
        selected = (selected * ((num_questions // len(selected)) + 1))[:num_questions]

    return [
        Question(
            id=str(uuid.uuid4()),
            question=q["question"],
            category=q["category"],
            difficulty=difficulty,
            expected_concepts=q["expected_concepts"],
            ideal_answer_hint=q["ideal_answer_hint"]
        )
        for q in selected[:num_questions]
    ]
