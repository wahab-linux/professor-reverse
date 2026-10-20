from pathlib import Path
from threading import Event

import pypdfium2 as pdfium
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter

from inversion import PDFError, invert_pdf, preview, render_page


@pytest.fixture
def source(tmp_path):
    image = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 140, 140), fill="black")
    draw.rectangle((220, 40, 320, 140), fill="red")
    path = tmp_path / "original.pdf"
    image.save(path, "PDF", resolution=72, save_all=True, append_images=[Image.new("RGB", (200, 400), "white")])
    return path


def test_inversion_and_page_geometry(source, tmp_path):
    target = tmp_path / "inverted.pdf"
    original_bytes = source.read_bytes()
    progress = []
    invert_pdf(source, target, 150, lambda done, total: progress.append((done, total)))
    assert source.read_bytes() == original_bytes
    assert progress == [(1, 2), (2, 2)]
    original, output = PdfReader(source), PdfReader(target)
    assert len(output.pages) == 2
    for before, after in zip(original.pages, output.pages):
        assert abs(float(before.mediabox.width) - float(after.mediabox.width)) < 1
        assert abs(float(before.mediabox.height) - float(after.mediabox.height)) < 1
    with pdfium.PdfDocument(target) as doc:
        image = render_page(doc, 0, 1)
    assert max(image.getpixel((15, 15))) < 15
    assert min(image.getpixel((80, 80))) > 240
    red, green, blue = image.getpixel((260, 80))
    assert red < 20 and green > 230 and blue > 230


def test_preview(source):
    before, after, count = preview(source)
    assert count == 2
    assert before.size == after.size
    a, b = before.getpixel((10, 10)), after.getpixel((10, 10))
    assert all(x + y == 255 for x, y in zip(a, b))


def test_original_cannot_be_overwritten(source):
    contents = source.read_bytes()
    with pytest.raises(PDFError, match="different filename"):
        invert_pdf(source, source)
    assert source.read_bytes() == contents


def test_cancel_keeps_existing_output(source, tmp_path):
    target = tmp_path / "existing.pdf"
    target.write_bytes(b"keep me")
    cancel = Event()
    def progress(done, total):
        cancel.set()
    with pytest.raises(PDFError, match="cancelled"):
        invert_pdf(source, target, progress=progress, cancel=cancel)
    assert target.read_bytes() == b"keep me"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["existing.pdf", "original.pdf"]


def test_invalid_and_encrypted_documents(tmp_path):
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a pdf")
    with pytest.raises(PDFError, match="Could not open"):
        preview(invalid)
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    writer.encrypt("password")
    locked = tmp_path / "locked.pdf"
    writer.write(locked)
    with pytest.raises(PDFError, match="password-protected"):
        preview(locked)


def test_render_failure_keeps_existing_output(source, tmp_path):
    huge = tmp_path / "huge.pdf"
    writer = PdfWriter()
    writer.add_blank_page(20000, 20000)
    writer.write(huge)
    target = tmp_path / "output.pdf"
    target.write_bytes(b"untouched")
    with pytest.raises(PDFError, match="too large"):
        invert_pdf(huge, target)
    assert target.read_bytes() == b"untouched"
