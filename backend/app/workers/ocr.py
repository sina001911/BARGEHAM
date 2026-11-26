"""OCR extraction worker: file → text chunks → embedding queue."""
from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import delete, func

from app.celery import celery_app
from app.classification.service import classify_document
from app.documents.models import Document, DocumentStatus, TextChunk
from app.duplicates.service import DuplicateDetector, compute_minhash, sha256_hash
from app.ocr import chunk_pages, extract_document
from app.storage import get_storage
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.ocr.process_document",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def process_document(self, document_id: str) -> dict:
    """Extract text from a document, persist chunks, and queue embeddings."""
    return run_async(_process_document(uuid.UUID(document_id)))


async def _process_document(document_id: uuid.UUID) -> dict:
    async with worker_session() as session:
        doc = await session.get(Document, document_id)
        if doc is None:
            logger.warning("OCR: document %s not found", document_id)
            return {"document_id": str(document_id), "status": "not_found"}

        try:
            data = get_storage().get_object(doc.storage_path)
            result = extract_document(data, doc.mime_type, doc.file_name)
        except Exception as exc:
            logger.exception("OCR: extraction error for %s: %s", document_id, exc)
            doc.status = DocumentStatus.OCR_FAILED
            session.add(doc)
            await session.commit()
            return {"document_id": str(document_id), "status": "ocr_failed"}

        # Replace any previous chunks (re-processing / new version).
        await session.execute(
            delete(TextChunk).where(TextChunk.document_id == document_id)
        )

        pieces = chunk_pages(
            [(p.page_number, p.text) for p in result.pages]
        )
        chunks: list[TextChunk] = []
        for piece in pieces:
            chunk = TextChunk(
                document_id=document_id,
                chunk_index=piece.chunk_index,
                text=piece.text,
                page_number=piece.page_number,
                direction=piece.direction,
                tsv=func.to_tsvector("simple", piece.text),
            )
            session.add(chunk)
            chunks.append(chunk)

        doc.page_count = max((p.page_number for p in result.pages), default=0) or None
        doc.language = result.language
        doc.has_text_layer = result.has_text_layer
        doc.ocr_confidence = result.confidence
        doc.status = DocumentStatus.READY if pieces else DocumentStatus.OCR_FAILED
        session.add(doc)

        # Generate embeddings off the event loop (model load + encode are sync),
        # but never block OCR: if embedding fails the document is still READY and
        # full-text searchable; vector search simply falls back to FTS.
        if chunks:
            from app.ai.embeddings import embed_texts

            try:
                loop = asyncio.get_running_loop()
                vectors = await loop.run_in_executor(
                    None, lambda: embed_texts([c.text for c in chunks])
                )
                for chunk, vector in zip(chunks, vectors):
                    chunk.embedding = vector
            except Exception as exc:  # pragma: no cover - model unavailable
                logger.warning("Embedding failed for %s: %s", document_id, exc)

        await session.commit()

        logger.info(
            "OCR: %s → %d chunks (lang=%s, text_layer=%s)",
            document_id,
            len(chunks),
            result.language,
            result.has_text_layer,
        )

        # Classification + duplicate detection after OCR
        text = "\n".join(p.text for p in result.pages if p.text)
        try:
            category, confidence = classify_document(text)
            if category is not None:
                doc.classification = category
                doc.classification_confidence = confidence
                doc.classification_version = (doc.classification_version or 0) + 1
                session.add(doc)
                await session.commit()
                logger.info(
                    "Classification: %s → %s (conf=%.3f)",
                    document_id,
                    category,
                    confidence or 0,
                )
        except Exception as exc:
            logger.warning("Classification failed for %s: %s", document_id, exc)

        # Duplicate detection
        try:
            data = get_storage().get_object(doc.storage_path)
            content_hash = sha256_hash(data)
            mh = compute_minhash(text)
            detector = DuplicateDetector()

            existing_hash = detector.check_exact(content_hash)
            if existing_hash is not None:
                doc.duplicate_of = uuid.UUID(existing_hash)
                doc.duplicate_similarity = 1.0
                doc.status = DocumentStatus.DUPLICATE
                session.add(doc)
                await session.commit()
                logger.info(
                    "Duplicate: %s is exact duplicate of %s",
                    document_id,
                    existing_hash,
                )
            else:
                near_id, sim = detector.check_near_duplicate(str(document_id), mh)
                if near_id is not None:
                    doc.duplicate_of = uuid.UUID(near_id)
                    doc.duplicate_similarity = sim
                    session.add(doc)
                    await session.commit()
                    logger.info(
                        "Duplicate: %s is near-duplicate of %s (sim=%.3f)",
                        document_id,
                        near_id,
                        sim,
                    )

            detector.register(str(document_id), content_hash, mh)
        except Exception as exc:
            logger.warning("Duplicate detection failed for %s: %s", document_id, exc)

        return {
            "document_id": str(document_id),
            "status": doc.status.value,
            "chunks": len(chunks),
            "language": result.language,
        }
