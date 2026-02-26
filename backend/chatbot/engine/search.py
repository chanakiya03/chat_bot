"""
Semantic Search Engine
Uses sentence-transformers to embed queries and find the most relevant
documents from the knowledge base using cosine similarity.
"""
import logging
import numpy as np
from .loader import get_knowledge_base

logger = logging.getLogger(__name__)

# Lazy-loaded model and embeddings
_model = None
_doc_embeddings = None
_warmed_up = False


def warm_up():
    """Pre-warm BERT model + doc embeddings in a background thread at startup."""
    import threading
    def _do_warm():
        global _warmed_up
        try:
            logger.info("[Warm-up] Pre-loading BERT model and doc embeddings...")
            _get_model()
            _get_doc_embeddings()
            _warmed_up = True
            logger.info("[Warm-up] Done. First requests will now be instant.")
        except Exception as e:
            logger.warning(f"[Warm-up] Failed (non-fatal): {e}")
    t = threading.Thread(target=_do_warm, daemon=True)
    t.start()


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)…")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Could not load sentence-transformers: {e}")
            _model = None
    return _model


def _get_doc_embeddings():
    global _doc_embeddings
    if _doc_embeddings is None:
        model = _get_model()
        if model is None:
            return None
        kb = get_knowledge_base()
        texts = [doc['text'] for doc in kb['documents']]
        logger.info(f"Encoding {len(texts)} documents…")
        _doc_embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        logger.info("Document embeddings ready.")
    return _doc_embeddings


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors or matrix."""
    if len(b.shape) == 1:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    norms = np.linalg.norm(b, axis=1) * np.linalg.norm(a) + 1e-10
    return np.dot(b, a) / norms


def semantic_search(query: str, top_k: int = 6):
    """
    Search the knowledge base for documents relevant to `query`.
    Returns list of (score, document) sorted by descending similarity.
    Falls back to keyword search if sentence-transformers unavailable.
    """
    model = _get_model()
    doc_embeddings = _get_doc_embeddings()
    kb = get_knowledge_base()
    documents = kb['documents']

    if model is not None and doc_embeddings is not None:
        # Semantic search
        query_embedding = model.encode([query], convert_to_numpy=True)[0]
        scores = _cosine_similarity(query_embedding, doc_embeddings)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(float(scores[i]), documents[i]) for i in top_indices]
    else:
        # Keyword fallback
        query_lower = query.lower()
        keywords = query_lower.split()
        scored = []
        for doc in documents:
            text_lower = doc['text'].lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:top_k]

    return [(score, doc) for score, doc in results if score > 0]
