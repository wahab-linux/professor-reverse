# Professor Reverse

A different shade of reading. A local Python desktop app to invert PDF colors, with a rounded, Earl Gray-inspired interface, light/dark themes, and real before/after previews.

## Run

Use Python 3.10 or newer with Tcl/Tk installed (included with the standard Windows Python installer).

```sh
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

On Linux, your distribution's `python3-tk` package and a graphical desktop are required. On macOS, use a Python distribution that includes Tk.

1. Click **Open PDF** (or Ctrl+O) and select a document.
2. Browse its pages with the arrows. Compare the original and inverted previews.
3. Choose an export resolution (150 DPI by default), then **Invert & save PDF**. Choose a location in the native Save As dialog.

White becomes black, black becomes white, and all other colors are inverted too, including images and visible annotations. The original is never overwritten. Files stay on your computer; no server, account, or network connection is needed.

## Export details

The app renders and inverts each page locally, then writes a new PDF. Page dimensions and order are preserved. **The exported pages are images:** selectable text, links, bookmarks, editable forms, and accessibility structure are not retained. Higher resolutions produce sharper pages and larger files. Output images use JPEG compression, so colors may have small compression differences. Previews use a smaller resolution independently of export quality.

Encrypted PDFs must be unlocked first. Unreadable and empty documents show an error. Extremely large pages have a 40-million-pixel render limit; reduce export DPI if necessary. Processing runs in a worker so the interface stays responsive. Closing during export cancels after the current page; an unfinished export is discarded. Output is replaced atomically only after successful processing.

## Tests

```sh
python -m pip install pytest
python -m pytest -q
```

Tests check actual rendered output colors, multipage output and dimensions, preview inversion, original-file protection, cancellation, malformed/password-protected PDFs, and failed-export safety.

Visual design inspired by [Earl Gray](https://github.com/wahab-linux/earl-gray); this is a standalone implementation.
