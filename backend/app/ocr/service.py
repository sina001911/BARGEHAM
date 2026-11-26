"""Text extraction for PDF, DOCX, XLSX, TXT, and images.

PaddleOCR is used when available (best Persian support), falling back to
Tesseract via ``pytesseract``. PDFs with an embedded text layer are read
directly with pdfplumber; otherwise pages are rasterised and OCR'd.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field

from app.config import settings
from app.ocr.chunking import detect_direction

logger = logging.getLogger(__name__)

_PDF_TEXT_LAYER_MIN_CHARS = 40  # below this per-page we treat it as scanned


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage] = field(default_factory=list)
    language: str = "und"
    confidence: float | None = None
    has_text_layer: bool = False
    direction: str = "ltr"

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)


# --------------------------------------------------------------------------- #
# Engine availability (lazy imports keep the app importable without heavy deps)
# --------------------------------------------------------------------------- #
def _load_paddleocr(lang: str):
    try:
        from paddleocr import PaddleOCR

        return PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("PaddleOCR unavailable: %s", exc)
        return None


def _load_tesseract():
    try:
        import pytesseract

        return pytesseract
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("pytesseract unavailable: %s", exc)
        return None


def _ocr_image_bytes(data: bytes) -> tuple[str, float | None]:
    """OCR a single image, returning text and mean confidence."""
    paddle_lang = "fa" if "fas" in settings.ocr_languages else "en"
    ocr = _load_paddleocr(paddle_lang)
    if ocr is not None:
        try:
            import numpy as np
            from PIL import Image

            image = Image.open(io.BytesIO(data)).convert("RGB")
            result = ocr.ocr(np.array(image))
            lines: list[str] = []
            scores: list[float] = []
            for page in result or []:
                for entry in page or []:
                    text, score = entry[1][0], float(entry[1][1])
                    lines.append(text)
                    scores.append(score)
            if lines:
                confidence = sum(scores) / len(scores)
                return "\n".join(lines), confidence
        except Exception as exc:  # pragma: no cover
            logger.debug("PaddleOCR failed, trying tesseract: %s", exc)

    tesseract = _load_tesseract()
    if tesseract is not None:
        try:
            from PIL import Image

            image = Image.open(io.BytesIO(data)).convert("RGB")
            lang = settings.ocr_languages.replace("+", "+")
            text = tesseract.image_to_string(image, lang=lang).strip()
            data_map = tesseract.image_to_data(
                image, lang=lang, output_type=tesseract.Output.DICT
            )
            confs = [float(c) for c in data_map.get("conf", []) if str(c) not in ("-1", "")]
            confidence = (sum(confs) / len(confs) / 100.0) if confs else None
            return text, confidence
        except Exception as exc:  # pragma: no cover
            logger.warning("Tesseract OCR failed: %s", exc)

    logger.warning("No OCR engine available; returning empty text for image")
    return "", None


# --------------------------------------------------------------------------- #
# Per-format extractors
# --------------------------------------------------------------------------- #
def _extract_pdf(data: bytes) -> ExtractionResult:
    import pdfplumber

    pages: list[ExtractedPage] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if len(text) >= _PDF_TEXT_LAYER_MIN_CHARS:
                pages.append(ExtractedPage(page_number=number, text=text))

    if pages:
        result = ExtractionResult(pages=pages, has_text_layer=True)
        _finalise(result)
        return result

    # Scanned PDF → rasterise and OCR.
    confidences: list[float] = []
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(data, dpi=200)
        for number, image in enumerate(images, start=1):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            text, conf = _ocr_image_bytes(buf.getvalue())
            pages.append(ExtractedPage(page_number=number, text=text))
            if conf is not None:
                confidences.append(conf)
    except Exception as exc:  # pragma: no cover
        logger.warning("PDF rasterisation failed: %s", exc)

    result = ExtractionResult(
        pages=pages,
        has_text_layer=False,
        confidence=(sum(confidences) / len(confidences)) if confidences else None,
    )
    _finalise(result)
    return result


def _extract_docx(data: bytes) -> ExtractionResult:
    import docx

    document = docx.Document(io.BytesIO(data))
    text_parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                text_parts.append(" | ".join(cells))
    result = ExtractionResult(
        pages=[ExtractedPage(page_number=1, text="\n".join(text_parts))],
        has_text_layer=True,
    )
    _finalise(result)
    return result


def _extract_xlsx(data: bytes) -> ExtractionResult:
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    pages: list[ExtractedPage] = []
    for number, sheet in enumerate(workbook.worksheets, start=1):
        rows: list[str] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(cell) for cell in row if cell is not None]
            if cells:
                rows.append(" | ".join(cells))
        pages.append(ExtractedPage(page_number=number, text="\n".join(rows)))
    workbook.close()
    result = ExtractionResult(pages=pages, has_text_layer=True)
    _finalise(result)
    return result


def _extract_txt(data: bytes) -> ExtractionResult:
    text = data.decode("utf-8", errors="replace")
    result = ExtractionResult(
        pages=[ExtractedPage(page_number=1, text=text)], has_text_layer=True
    )
    _finalise(result)
    return result


def _extract_image(data: bytes) -> ExtractionResult:
    text, confidence = _ocr_image_bytes(data)
    result = ExtractionResult(
        pages=[ExtractedPage(page_number=1, text=text)],
        confidence=confidence,
        has_text_layer=False,
    )
    _finalise(result)
    return result


def _finalise(result: ExtractionResult) -> None:
    """Populate language and direction from the extracted text."""
    sample = result.full_text[:4000]
    result.direction = detect_direction(sample)
    result.language = "fa" if result.direction == "rtl" else "en"
    if result.direction == "rtl" and "eng" in settings.ocr_languages:
        # Bilingual documents: keep 'fa' but the flag above drives UI direction.
        result.language = "fa"


_DISPATCH = {
    "application/pdf": _extract_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": _extract_docx,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": _extract_xlsx,
    "text/plain": _extract_txt,
    "image/png": _extract_image,
    "image/jpeg": _extract_image,
    "image/tiff": _extract_image,
    "image/webp": _extract_image,
}


def extract_document(data: bytes, mime_type: str, file_name: str) -> ExtractionResult:
    """Extract text from a document, dispatching on MIME type / extension."""
    handler = _DISPATCH.get(mime_type)
    if handler is None:
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        handler = {
            "pdf": _extract_pdf,
            "docx": _extract_docx,
            "xlsx": _extract_xlsx,
            "txt": _extract_txt,
            "png": _extract_image,
            "jpg": _extract_image,
            "jpeg": _extract_image,
            "tif": _extract_image,
            "tiff": _extract_image,
            "webp": _extract_image,
        }.get(ext)
    if handler is None:
        logger.warning("Unsupported document type: %s (%s)", mime_type, file_name)
        return ExtractionResult(pages=[], language="und")

    try:
        return handler(data)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Extraction failed for %s: %s", file_name, exc)
        return ExtractionResult(pages=[], language="und")
