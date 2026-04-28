import numpy as np
from typing import List, Optional
import os

_model = None
_model_name = "all-MiniLM-L6-v2"


def get_model():
    """Lazy-load the Sentence Transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_model_name)
            print(f"[Embedder] Loaded {_model_name}")
        except ImportError:
            print("[Embedder] sentence-transformers not installed. Using TF-IDF fallback.")
            _model = "tfidf"
    return _model


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string into a vector."""
    model = get_model()
    if model == "tfidf":
        return _tfidf_embed(text)
    return model.encode(text, convert_to_numpy=True, normalize_embeddings=True)


def embed_batch(texts: List[str]) -> np.ndarray:
    """Embed multiple texts efficiently."""
    model = get_model()
    if model == "tfidf":
        return np.vstack([_tfidf_embed(t) for t in texts])
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def compute_resume_jd_similarity(resume_text: str, jd_text: str) -> float:
    """Compute semantic similarity between resume and job description."""
    # Use chunked similarity for long texts
    resume_chunks = _chunk_text(resume_text, max_chars=512)
    jd_chunks = _chunk_text(jd_text, max_chars=512)

    resume_vecs = embed_batch(resume_chunks)
    jd_vecs = embed_batch(jd_chunks)

    # Max pooling across chunks (best match)
    resume_vec = np.max(resume_vecs, axis=0)
    jd_vec = np.max(jd_vecs, axis=0)

    sim = cosine_similarity(resume_vec, jd_vec)
    return round(float(sim), 4)


def compute_answer_similarity(user_answer: str, ideal_answer: str) -> float:
    """Compute how similar a user's answer is to the ideal answer."""
    if not user_answer.strip() or not ideal_answer.strip():
        return 0.0
    vec_user = embed_text(user_answer)
    vec_ideal = embed_text(ideal_answer)
    sim = cosine_similarity(vec_user, vec_ideal)
    return round(float(sim), 4)


def find_similar_skills(skill: str, skill_list: List[str], top_k: int = 3) -> List[str]:
    """Find semantically similar skills from a list."""
    if not skill_list:
        return []
    vecs = embed_batch([skill] + skill_list)
    skill_vec = vecs[0]
    sims = [cosine_similarity(skill_vec, vecs[i+1]) for i in range(len(skill_list))]
    ranked = sorted(zip(sims, skill_list), reverse=True)
    return [s for _, s in ranked[:top_k] if _ > 0.5]


def _chunk_text(text: str, max_chars: int = 512) -> List[str]:
    """Split text into chunks for embedding."""
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) > max_chars and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks or [text[:max_chars]]


def _tfidf_embed(text: str) -> np.ndarray:
    """TF-IDF fallback embedding when sentence-transformers not available."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    import hashlib
    # Create a simple hash-based vector (64-dim)
    words = text.lower().split()
    vec = np.zeros(64)
    for i, word in enumerate(words[:200]):
        idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % 64
        vec[idx] += 1.0 / (i + 1)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec
