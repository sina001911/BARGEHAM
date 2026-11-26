"""Document classification service using zero-shot NLI models.

Classifies documents into categories: contract, invoice, receipt, report,
book, personal_document, technical_document, correspondence, other.

Uses sentence-transformers zero-shot NLI: given a document excerpt and a
candidate label, the model scores whether the text "entails" the label.
The highest-scoring label above the confidence threshold is selected.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_CATEGORIES: list[str] | None = None
_model = None
_lock = False  # simple re-entrancy guard for lazy loading


def _get_categories() -> list[str]:
    """Parse configured classification categories."""
    global _CATEGORIES
    if _CATEGORIES is None:
        _CATEGORIES = [
            c.strip() for c in settings.classification_categories.split(",") if c.strip()
        ]
    return _CATEGORIES


def _get_model():
    """Lazy-load the zero-shot NLI model on first use."""
    global _model, _lock
    if _model is not None:
        return _model
    if _lock:
        return None  # another coroutine is loading; skip
    _lock = True
    try:
        from sentence_transformers import CrossEncoder

        # Cross-encoder NLI: text + label -> entailment score
        _model = CrossEncoder("cross-encoder/nli-roberta-base")
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("Zero-shot classifier unavailable: %s", exc)
        _model = None
    finally:
        _lock = False
    return _model


def classify_document(text: str) -> tuple[str | None, float | None]:
    """Classify a document's text into a category.

    Returns (category, confidence) or (None, None) if classification
    is disabled or the model is unavailable.
    """
    if not settings.classification_enabled:
        return None, None

    categories = _get_categories()
    if not categories:
        return None, None

    model = _get_model()
    if model is None:
        logger.warning("Classification model not loaded; skipping")
        return None, None

    if not text or not text.strip():
        return None, None

    # Truncate to fit model context (cross-encoders are sensitive to length)
    excerpt = text[:2000]

    # Build premise/hypothesis pairs for NLI
    pairs = [(excerpt, f"This document is about {cat}.") for cat in categories]

    # Apply sigmoid to get probabilities in [0, 1]
    import numpy as np

    try:
        import math

        raw_scores = model.predict(pairs, show_progress_bar=False)
        scores_arr = np.asarray(raw_scores, dtype=float).ravel()
        probs = [(1.0 / (1.0 + math.exp(-float(s)))) for s in scores_arr]
    except Exception as exc:
        logger.warning("Classification computation failed: %s", exc)
        return None, None

    if not probs:
        return None, None

    try:
        best_idx = max(range(len(probs)), key=lambda i: probs[i])
        best_cat = categories[best_idx]
        best_conf = float(probs[best_idx])
    except Exception as exc:
        logger.warning("Classification scoring failed: %s", exc)
        return None, None

    if best_conf < settings.classification_confidence_threshold:
        return "other", best_conf

    return best_cat, best_conf


def batch_classify(texts: list[str]) -> list[tuple[str | None, float | None]]:
    """Classify multiple documents efficiently in one batch."""
    if not settings.classification_enabled:
        return [(None, None) for _ in texts]

    categories = _get_categories()
    if not categories:
        return [(None, None) for _ in texts]

    model = _get_model()
    if model is None:
        return [(None, None) for _ in texts]

    # Build all pairs
    pairs: list[tuple[str, str]] = []
    valid_idx: list[int] = []
    for i, text in enumerate(texts):
        if text and text.strip():
            excerpt = text[:2000]
            for cat in categories:
                pairs.append((excerpt, f"This document is about {cat}."))
            valid_idx.append(i)

    if not pairs:
        return [(None, None) for _ in texts]

    try:
        import math

        scores = model.predict(pairs, show_progress_bar=False)
    except Exception as exc:  # pragma: no cover
        logger.warning("Batch classification failed: %s", exc)
        return [(None, None) for _ in texts]

    results: list[tuple[str | None, float | None]] = [(None, None)] * len(texts)
    n_cats = len(categories)
    pos = 0
    for i in valid_idx:
        cat_probs = []
        for j in range(n_cats):
            p = 1.0 / (1.0 + math.exp(-float(scores[pos + j])))
            cat_probs.append(p)
        pos += n_cats

        best_idx = max(range(n_cats), key=lambda k: cat_probs[k])
        best_cat = categories[best_idx]
        best_conf = cat_probs[best_idx]

        if best_conf < settings.classification_confidence_threshold:
            best_cat = "other"

        results[i] = (best_cat, best_conf)

    return results
