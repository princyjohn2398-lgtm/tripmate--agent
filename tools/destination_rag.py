"""Lightweight RAG-style retrieval over the supplied destination text files.

Uses TF-IDF similarity (not an embedding model). Each chunk is tagged with its
city, and if the query names a known city or country, only that city is searched.
"""
from functools import lru_cache
from pathlib import Path
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "destinations"
HEADING = re.compile(r"(?m)^(?=[A-Z][A-Z &/-]{3,}$)")


def _load_chunks(data_dir: Path = DATA_DIR):
    chunks = []
    if not data_dir.exists():
        return chunks
    for path in sorted(data_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"DESTINATION GUIDE:\s*(.+)", text)
        if not match:
            continue  # skips placeholder files without a guide header
        label = match.group(1).strip().title()  # e.g. "Bangkok, Thailand"
        names = {part.strip().lower() for part in label.split(",")}
        for section in HEADING.split(text):
            section = section.strip()
            if len(section) > 35 and not section.startswith("DESTINATION GUIDE"):
                chunks.append({
                    "source": path.name,
                    "names": names,
                    "text": f"{label}\n{section}",
                })
    return chunks


@lru_cache(maxsize=1)
def _index():
    chunks = _load_chunks()
    if not chunks:
        return chunks, None, None
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([c["text"] for c in chunks])
    return chunks, vectorizer, matrix


def search_destination_guide(query: str, top_k: int = 3) -> list[str]:
    """Return the most relevant destination-guide chunks for a natural-language query."""
    query = (query or "").strip()
    if not query:
        return []
    chunks, vectorizer, matrix = _index()
    if vectorizer is None:
        return []
    lowered = query.lower()
    matched = [
        i for i, c in enumerate(chunks)
        if any(re.search(rf"\b{re.escape(name)}\b", lowered) for name in c["names"])
    ]
    candidates = matched or list(range(len(chunks)))
    scores = cosine_similarity(vectorizer.transform([query]), matrix[candidates]).ravel()
    ranked = scores.argsort()[::-1][:max(1, top_k)]
    results = []
    for r in ranked:
        if scores[r] > 0:
            chunk = chunks[candidates[int(r)]]
            results.append(f"Source: {chunk['source']}\n{chunk['text']}")
    return results
