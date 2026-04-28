import re
import json
from typing import List, Dict, Optional, Tuple
from models.schemas import ExtractedProfile


# ─── Comprehensive skill taxonomy ────────────────────────────────────────────
SKILLS_DB = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "swift", "kotlin", "scala", "r", "matlab", "php", "perl",
        "dart", "elixir", "haskell", "lua", "assembly", "vba", "bash", "shell"
    ],
    "ml_ai": [
        "machine learning", "deep learning", "neural networks", "nlp",
        "natural language processing", "computer vision", "reinforcement learning",
        "transfer learning", "bert", "gpt", "transformers", "lstm", "cnn", "rnn",
        "generative ai", "llm", "diffusion models", "gans", "xgboost", "lightgbm",
        "random forest", "scikit-learn", "tensorflow", "pytorch", "keras",
        "huggingface", "langchain", "openai", "sentence transformers", "spacy",
        "nltk", "feature engineering", "model deployment", "mlops", "a/b testing",
        "recommendation systems", "anomaly detection", "time series forecasting"
    ],
    "data": [
        "pandas", "numpy", "sql", "nosql", "mongodb", "postgresql", "mysql",
        "sqlite", "redis", "elasticsearch", "apache spark", "hadoop", "kafka",
        "airflow", "dbt", "tableau", "power bi", "data pipeline", "etl",
        "data warehousing", "snowflake", "bigquery", "databricks", "pyspark",
        "data visualization", "matplotlib", "seaborn", "plotly", "d3.js"
    ],
    "web_frontend": [
        "react", "angular", "vue", "next.js", "nuxt", "html", "css", "sass",
        "tailwind", "bootstrap", "material ui", "redux", "graphql", "rest api",
        "webpack", "vite", "typescript", "javascript", "jquery", "svelte"
    ],
    "web_backend": [
        "node.js", "express", "fastapi", "django", "flask", "spring boot",
        "laravel", "rails", "asp.net", "grpc", "microservices", "api design",
        "oauth", "jwt", "websockets", "kafka", "rabbitmq", "celery"
    ],
    "cloud_devops": [
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "github actions", "gitlab ci", "ci/cd", "linux", "nginx",
        "load balancing", "serverless", "lambda", "ec2", "s3", "cloudformation",
        "helm", "prometheus", "grafana", "datadog", "elk stack"
    ],
    "mobile": [
        "android", "ios", "react native", "flutter", "swift", "kotlin",
        "xamarin", "ionic", "cordova", "firebase"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "agile", "scrum", "kanban", "jira", "confluence", "project management"
    ]
}

ALL_SKILLS = []
for category_skills in SKILLS_DB.values():
    ALL_SKILLS.extend(category_skills)

EDUCATION_LEVELS = {
    "phd": 5, "ph.d": 5, "doctorate": 5,
    "master": 4, "m.tech": 4, "m.e": 4, "mba": 4, "m.sc": 4, "ms": 4, "m.s": 4,
    "bachelor": 3, "b.tech": 3, "b.e": 3, "b.sc": 3, "b.s": 3, "undergraduate": 3,
    "diploma": 2, "associate": 2,
    "12th": 1, "high school": 1, "hsc": 1
}

EXPERIENCE_PATTERNS = [
    r'(\d+\.?\d*)\+?\s*years?\s+(?:of\s+)?experience',
    r'(\d+\.?\d*)\+?\s*yrs?\s+(?:of\s+)?experience',
    r'experience[:\s]+(\d+\.?\d*)\+?\s*years?',
    r'(\d{4})\s*[-–]\s*(?:present|current|now)',
    r'worked?\s+(?:for\s+)?(\d+\.?\d*)\s*years?',
]

PROJECT_COMPLEXITY_KEYWORDS = {
    "high": ["production", "scalable", "distributed", "real-time", "deployed",
              "million users", "microservices", "cloud", "enterprise", "published",
              "patent", "research paper", "open source"],
    "medium": ["api", "database", "machine learning", "full stack", "backend",
               "frontend", "mobile app", "web app", "automation", "pipeline"],
    "low": ["project", "assignment", "basic", "simple", "tutorial", "practice"]
}


def extract_skills(text: str) -> List[str]:
    """Extract skills using pattern matching against taxonomy."""
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        # Use word boundary matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill.title() if len(skill) > 3 else skill.upper())
    # Deduplicate preserving order
    seen = set()
    unique = []
    for s in found:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique.append(s)
    return unique


def extract_experience(text: str) -> float:
    """Extract years of experience from resume text."""
    text_lower = text.lower()

    # Try explicit year mentions
    for pattern in EXPERIENCE_PATTERNS[:3]:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                pass

    # Calculate from date ranges (e.g., "2020 - Present")
    date_pattern = r'(\d{4})\s*[-–—]\s*(present|current|now|\d{4})'
    matches = re.findall(date_pattern, text_lower)
    if matches:
        import datetime
        current_year = datetime.datetime.now().year
        total_years = 0
        for start, end in matches:
            start_y = int(start)
            end_y = current_year if end in ["present", "current", "now"] else int(end)
            if 1990 <= start_y <= current_year and end_y >= start_y:
                total_years += end_y - start_y
        if total_years > 0:
            return min(total_years, 40.0)

    return 0.0


def extract_education(text: str) -> Tuple[str, Optional[str]]:
    """Extract education level and field from resume."""
    text_lower = text.lower()
    best_level = "Unknown"
    best_score = -1
    field = None

    for keyword, score in EDUCATION_LEVELS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            if score > best_score:
                best_score = score
                if score >= 4:
                    best_level = "Masters"
                elif score >= 3:
                    best_level = "Bachelors"
                elif score >= 5:
                    best_level = "PhD"
                elif score >= 2:
                    best_level = "Diploma"
                else:
                    best_level = "High School"

    # Map score back to label
    level_map = {5: "PhD", 4: "Masters", 3: "Bachelors", 2: "Diploma", 1: "High School"}
    best_level = level_map.get(best_score, "Unknown")

    # Try to extract field
    fields = ["computer science", "information technology", "electronics",
              "electrical engineering", "mechanical engineering", "data science",
              "artificial intelligence", "mathematics", "physics", "mba", "finance"]
    for f in fields:
        if f in text_lower:
            field = f.title()
            break

    return best_level, field


def extract_projects(text: str) -> List[str]:
    """Extract project names and descriptions from resume."""
    projects = []
    # Look for project sections
    project_section_pattern = r'(?:projects?|personal projects?|academic projects?)[:\n](.*?)(?=\n(?:experience|education|skills|certifications|work|employment)|$)'
    matches = re.findall(project_section_pattern, text.lower(), re.DOTALL | re.IGNORECASE)

    # Also look for bullet points starting with project-like terms
    bullet_pattern = r'[•\-\*]\s*([A-Z][^\n]{10,80})'
    bullet_matches = re.findall(bullet_pattern, text)

    if matches:
        # Extract individual project names
        for block in matches:
            lines = [l.strip() for l in block.split('\n') if l.strip() and len(l.strip()) > 5]
            projects.extend(lines[:5])
    elif bullet_matches:
        projects = bullet_matches[:8]

    return projects[:8]


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extract name, email, phone from resume."""
    info = {"name": None, "email": None, "phone": None}

    # Email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        info["email"] = email_match.group()

    # Phone
    phone_match = re.search(r'[\+]?[1-9][\d\s\-\(\)]{8,15}', text)
    if phone_match:
        raw = re.sub(r'\s+', '', phone_match.group())
        if len(raw) >= 10:
            info["phone"] = raw

    # Name — usually first 2-3 words on first line
    first_line = text.strip().split('\n')[0].strip()
    words = first_line.split()
    if 1 <= len(words) <= 4 and all(w.replace('.', '').isalpha() for w in words):
        info["name"] = first_line

    return info


def compute_project_complexity(text: str, projects: List[str]) -> float:
    """Score project complexity from 0-10."""
    text_lower = text.lower()
    score = 0.0

    high_count = sum(1 for kw in PROJECT_COMPLEXITY_KEYWORDS["high"] if kw in text_lower)
    med_count = sum(1 for kw in PROJECT_COMPLEXITY_KEYWORDS["medium"] if kw in text_lower)
    low_count = sum(1 for kw in PROJECT_COMPLEXITY_KEYWORDS["low"] if kw in text_lower)

    score += min(high_count * 2.0, 6.0)
    score += min(med_count * 0.8, 3.0)
    score += min(len(projects) * 0.5, 2.0)
    score -= min(low_count * 0.3, 1.0)

    return round(min(max(score, 0), 10), 2)


def extract_profile(text: str) -> ExtractedProfile:
    """Full pipeline: extract all profile info from resume text."""
    contact = extract_contact_info(text)
    skills = extract_skills(text)
    experience = extract_experience(text)
    education_level, education_field = extract_education(text)
    projects = extract_projects(text)
    complexity = compute_project_complexity(text, projects)

    return ExtractedProfile(
        name=contact.get("name"),
        email=contact.get("email"),
        phone=contact.get("phone"),
        skills=skills,
        experience_years=experience,
        education_level=education_level,
        education_field=education_field,
        projects=projects,
        project_complexity_score=complexity,
        raw_text=text
    )
