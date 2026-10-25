"""Lightweight RAG-style retrieval over the supplied destination text files.

This implementation uses TF-IDF similarity (not an embedding model). It is small,
local, and suitable for a technical-assessment prototype.
"""
from pathlib import Path
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "destinations"

def _load_chunks(data_dir: Path = DATA_DIR):
    chunks = []
    if not data_dir.exists():
        return chunks
    for path in sorted(data_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        # Split on uppercase guide section headings, preserving each section heading.
        sections = re.split(r"(?m)^(?=[A-Z][A-Z &/-]{3,}$)", text)
        for section in sections:
            section = section.strip()
            if len(section) > 35:
                chunks.append({"source": path.name, "text": section})
    return chunks

def search_destination_guide(query: str, top_k: int = 3) -> list[str]:
    """Return the most relevant destination-guide chunks for a natural-language query."""
    query = (query or "").strip()
    if not query:
        return []
    chunks = _load_chunks()
    if not chunks:
        return []
    documents = [item["text"] for item in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(documents + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    ranked = scores.argsort()[::-1][:max(1, top_k)]
    results = []
    for index in ranked:
        if scores[index] > 0:
            item = chunks[int(index)]
            results.append(f"Source: {item['source']}\n{item['text']}")
    return results
