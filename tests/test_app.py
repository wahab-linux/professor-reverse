"""Optional desktop smoke test: run with DISPLAY set on Linux."""
import os
import sys
import time
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

pytestmark = pytest.mark.skipif(sys.platform.startswith('linux') and not os.environ.get('DISPLAY'), reason='Requires a graphical display')


def test_desktop_workflow(tmp_path, monkeypatch):
    from app import App
    source = tmp_path / 'input.pdf'
    target = tmp_path / 'output.pdf'
    Image.new('RGB', (400, 500), 'white').save(source, 'PDF', save_all=True, append_images=[Image.new('RGB', (500, 300), 'black')])
    app = App()
    errors = []
    app.report_callback_exception = lambda *args: errors.append(str(args))
    monkeypatch.setattr('app.messagebox.showerror', lambda *args: errors.append(str(args)))
    def wait():
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            app.update()
            if not app.busy:
                break
            time.sleep(.02)
        assert not app.busy, 'UI operation timed out'
        assert not errors, errors
    try:
        app.update()
        assert app.save_button.cget('state') == 'disabled'
        monkeypatch.setattr('app.filedialog.askopenfilename', lambda **kwargs: str(source))
        app.open_file()
        wait()
        assert app.pages == 2 and app.path == source
        assert app.save_button.cget('state') == 'normal'
        app.theme()
        app.update()
        assert app.dark
        app.navigate(1)
        wait()
        assert app.page == 1
        monkeypatch.setattr('app.filedialog.asksaveasfilename', lambda **kwargs: str(target))
        app.save()
        wait()
        assert len(PdfReader(target).pages) == 2
        app.theme()
        app.clear()
        app.update()
        assert app.path is None
    finally:
        app.cancel.set()
        app.pool.shutdown(wait=True, cancel_futures=True)
        app.destroy()
