"""Unit tests for text chunking."""
from __future__ import annotations

from app.ocr.chunking import chunk_pages, detect_direction


def test_detect_direction_rtl():
    assert detect_direction("سلام دنیا") == "rtl"
    assert detect_direction("Hello world") == "ltr"


def test_chunk_pages_single_page():
    pages = [(1, "سلام دنیا. این یک متن تست است.")]
    pieces = chunk_pages(pages, chunk_size=50, overlap=5)
    assert len(pieces) >= 1
    assert pieces[0].page_number == 1


def test_chunk_pages_overlap():
    long_text = " ".join(["کلمه"] * 200)
    pages = [(1, long_text)]
    pieces = chunk_pages(pages, chunk_size=100, overlap=10)
    assert len(pieces) > 1


def test_chunk_pages_empty():
    pieces = chunk_pages([(1, "")])
    assert pieces == []


def test_chunk_pages_multiple_pages():
    pages = [(1, "صفحه اول"), (2, "صفحه دوم")]
    pieces = chunk_pages(pages, chunk_size=100)
    page_nums = {p.page_number for p in pieces}
    assert page_nums == {1, 2}


def test_index_sequential():
    pages = [(1, "یک")] * 3
    pieces = chunk_pages(pages, chunk_size=10)
    assert [p.chunk_index for p in pieces] == [0, 1, 2]
