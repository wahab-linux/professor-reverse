"""Local PDF rendering and atomic, page-by-page inversion."""
from io import BytesIO
import os
from pathlib import Path
import tempfile

import pypdfium2 as pdfium
from PIL import ImageOps
from pypdf import PdfReader, PdfWriter


class PDFError(ValueError):
    pass


def open_pdf(path):
    try:
        doc = pdfium.PdfDocument(str(path))
        if not len(doc):
            doc.close()
            raise PDFError("This PDF has no pages.")
        return doc
    except PDFError:
        raise
    except Exception as exc:
        raise PDFError("Could not open this PDF. It may be damaged or password-protected.") from exc


def render_page(doc, index, scale):
    page = doc[index]
    try:
        width, height = page.get_size()
        if width * height * scale * scale > 40_000_000:
            raise PDFError("This page is too large at this resolution. Choose a lower quality.")
        bitmap = page.render(scale=scale, draw_annots=True)
        try:
            return bitmap.to_pil().convert("RGB")
        finally:
            bitmap.close()
    finally:
        page.close()


def preview(path, index=0):
    with open_pdf(path) as doc:
        page = doc[index]
        try:
            scale = min(1.5, 560 / max(page.get_size()))
        finally:
            page.close()
        original = render_page(doc, index, scale)
        return original, ImageOps.invert(original), len(doc)


def invert_pdf(source, destination, dpi=150, progress=None, cancel=None):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise PDFError("Choose a different filename to keep your original safe.")
    if dpi not in (96, 150, 200, 300):
        raise PDFError("Unsupported resolution.")
    temp = None
    writer = PdfWriter()
    try:
        with open_pdf(source) as doc:
            for index in range(len(doc)):
                if cancel and cancel.is_set():
                    raise PDFError("Export cancelled. No output was saved.")
                image = render_page(doc, index, dpi / 72)
                inverted = ImageOps.invert(image)
                buffer = BytesIO()
                inverted.save(buffer, format="PDF", resolution=dpi)
                buffer.seek(0)
                writer.add_page(PdfReader(buffer).pages[0])
                image.close()
                inverted.close()
                if progress:
                    progress(index + 1, len(doc))
            writer.add_metadata({"/Title": source.stem + " — inverted", "/Creator": "Professor Reverse"})
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".pdf", delete=False) as handle:
                temp = Path(handle.name)
                writer.write(handle)
            if cancel and cancel.is_set():
                raise PDFError("Export cancelled. No output was saved.")
            os.replace(temp, destination)
            temp = None
    finally:
        writer.close()
        if temp is not None:
            temp.unlink(missing_ok=True)
