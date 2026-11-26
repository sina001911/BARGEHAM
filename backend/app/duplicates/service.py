"""Duplicate document detection: exact (SHA-256) + near-duplicate (MinHash + LSH).

Exact duplicates share the same content hash. Near-duplicates are detected
using MinHash signatures compared with Jaccard similarity threshold.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

from app.config import settings

logger = logging.getLogger(__name__)


def sha256_hash(data: bytes) -> str:
    """Return SHA-256 hex digest of document bytes (exact duplicate key)."""
    return hashlib.sha256(data).hexdigest()


@dataclass
class MinHash:
    """MinHash signature for near-duplicate detection."""

    num_perm: int = 128
    _hashes: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self._hashes:
            self._hashes = [2**64 - 1] * self.num_perm

    def update(self, token: str) -> None:
        """Add a token to the MinHash signature."""
        h = _hash_token(token)
        for i in range(self.num_perm):
            # Use different seed per permutation via XOR with prime
            seeded = h ^ ((i + 1) * 2654435761)
            if seeded < self._hashes[i]:
                self._hashes[i] = seeded

    def merge(self, other: "MinHash") -> None:
        """Merge another MinHash into this one (element-wise min)."""
        for i in range(self.num_perm):
            if other._hashes[i] < self._hashes[i]:
                self._hashes[i] = other._hashes[i]

    def jaccard(self, other: "MinHash") -> float:
        """Estimated Jaccard similarity with another MinHash."""
        if self.num_perm != other.num_perm:
            raise ValueError("MinHash permutations must match")
        matches = sum(1 for a, b in zip(self._hashes, other._hashes) if a == b)
        return matches / self.num_perm


def _hash_token(token: str) -> int:
    """Hash a token string to a 64-bit integer."""
    return int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)


def tokenize_text(text: str, ngram: int = 3) -> set[str]:
    """Tokenize text into character n-grams for MinHash."""
    if not text:
        return set()
    # Normalize whitespace for stable n-grams
    norm = " ".join(text.split())
    if len(norm) < ngram:
        return {norm} if norm else set()
    return {norm[i : i + ngram] for i in range(len(norm) - ngram + 1)}


def compute_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Compute MinHash signature for a text string."""
    mh = MinHash(num_perm=num_perm)
    for token in tokenize_text(text):
        mh.update(token)
    return mh


@dataclass
class DuplicateResult:
    """Result of duplicate detection."""

    is_exact_duplicate: bool = False
    exact_match_id: str | None = None
    is_near_duplicate: bool = False
    near_match_id: str | None = None
    near_similarity: float = 0.0
    content_hash: str = ""


class DuplicateDetector:
    """Detect exact and near-duplicate documents.

    Maintains an in-memory index of document hashes and MinHash signatures.
    In production this would be backed by Redis/PostgreSQL.
    """

    def __init__(self) -> None:
        self._hash_index: dict[str, str] = {}  # content_hash -> document_id
        self._minhash_index: dict[str, MinHash] = {}  # document_id -> MinHash
        self._threshold = settings.duplicate_similarity_threshold

    def check_exact(self, content_hash: str) -> str | None:
        """Return document_id if content_hash already exists (exact duplicate)."""
        return self._hash_index.get(content_hash)

    def check_near_duplicate(self, document_id: str, mh: MinHash) -> tuple[str | None, float]:
        """Find most similar existing document via MinHash Jaccard."""
        best_id: str | None = None
        best_sim = 0.0
        for existing_id, existing_mh in self._minhash_index.items():
            if existing_id == document_id:
                continue
            sim = mh.jaccard(existing_mh)
            if sim > best_sim:
                best_sim = sim
                best_id = existing_id
        if best_sim >= self._threshold:
            return best_id, best_sim
        return None, best_sim

    def register(self, document_id: str, content_hash: str, mh: MinHash) -> None:
        """Register a document in the duplicate index."""
        self._hash_index[content_hash] = document_id
        self._minhash_index[document_id] = mh

    def detect(
        self,
        document_id: str,
        content: bytes,
        text: str,
    ) -> DuplicateResult:
        """Run full duplicate detection: exact + near-duplicate."""
        content_hash = sha256_hash(content)
        result = DuplicateResult(
            is_exact_duplicate=False,
            exact_match_id=None,
            is_near_duplicate=False,
            near_match_id=None,
            near_similarity=0.0,
            content_hash=content_hash,
        )

        if not settings.duplicate_detection_enabled:
            return result

        # Exact match check
        existing = self.check_exact(content_hash)
        if existing is not None:
            result.is_exact_duplicate = True
            result.exact_match_id = existing
            return result

        # Near-duplicate check
        mh = compute_minhash(text)
        near_id, sim = self.check_near_duplicate(document_id, mh)
        if near_id is not None:
            result.is_near_duplicate = True
            result.near_match_id = near_id
            result.near_similarity = sim

        # Register regardless (for future comparisons)
        self.register(document_id, content_hash, mh)
        return result


# Module-level singleton detector
_detector: DuplicateDetector | None = None


def get_detector() -> DuplicateDetector:
    """Return the module-level duplicate detector (singleton)."""
    global _detector
    if _detector is None:
        _detector = DuplicateDetector()
    return _detector
