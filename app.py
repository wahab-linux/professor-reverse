"""Professor Reverse — a local desktop PDF color inverter."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue, Empty
from threading import Event
from tkinter import filedialog, messagebox, font

import customtkinter as ctk
from inversion import preview, invert_pdf

BG = ("#F4F7FC", "#11151E")
SURFACE = ("#FFFFFF", "#1B2230")
SOFT = ("#EBF0F8", "#252F40")
INK = ("#202B40", "#EDF2FC")
MUTED = ("#647189", "#A3B0C6")
BLUE = "#1967D2"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("Professor Reverse | A different shade of reading")
        self.geometry("1120x800")
        self.minsize(940, 720)
        self.configure(fg_color=BG)
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.events = Queue()
        self.cancel = Event()
        self.path = None
        self.page = 0
        self.pages = 0
        self.busy = False
        self.dark = False
        self.photos = []
        families = set(font.families(self))
        self.family = next((name for name in ("Segoe UI", "DejaVu Sans", "Helvetica") if name in families), "Arial")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        sidebar = ctk.CTkFrame(self, width=218, corner_radius=0, fg_color=SURFACE)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(5, weight=1)
        self.label(sidebar, "◐  professor\n     reverse", 24, True).grid(row=0, column=0, padx=22, pady=(30, 8), sticky="w")
        self.label(sidebar, "A DIFFERENT SHADE OF READING", 10, color=MUTED).grid(row=1, column=0, pady=(0, 28))
        self.open_button = ctk.CTkButton(sidebar, text="＋  Open PDF", height=44, corner_radius=16, fg_color=BLUE, command=self.open_file)
        self.open_button.grid(row=2, column=0, padx=20, sticky="ew")
        steps = ctk.CTkFrame(sidebar, fg_color=BG, corner_radius=20)
        steps.grid(row=3, column=0, padx=20, pady=24, sticky="ew")
        self.label(steps, "THREE LITTLE STEPS", 10, color=MUTED).pack(pady=(18, 10))
        for text in ("①  Bring your PDF", "②  Preview the flip", "③  Save a darker copy"):
            self.label(steps, text, 12).pack(anchor="w", padx=15, pady=9)
        self.label(steps, "", 4).pack()
        self.label(sidebar, "Private by default\n\nNo uploads. No accounts.\nJust you and your pages.", 12, color=MUTED).grid(row=6, column=0, padx=22, pady=20, sticky="w")
        self.clear_button = ctk.CTkButton(sidebar, text="Clear workspace", fg_color=SOFT, text_color=INK, corner_radius=14, command=self.clear)
        self.clear_button.grid(row=7, column=0, padx=20, pady=(0, 22), sticky="ew")
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, padx=26, pady=24, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        self.label(header, "Your PDF. A new perspective.", 28, True).pack(side="left")
        self.theme_button = ctk.CTkButton(header, text="Dark", width=58, height=38, corner_radius=19, fg_color=SOFT, text_color=INK, command=self.theme)
        self.theme_button.pack(side="right")
        self.label(main, "Less glare. Same ideas. Every color, reversed.", 13, color=MUTED).grid(row=1, column=0, sticky="w", pady=(4, 20))
        self.filename = self.label(main, "Open a PDF to get started", 15, True)
        self.filename.grid(row=2, column=0, sticky="w", pady=(0, 12))
        previews = ctk.CTkFrame(main, fg_color="transparent")
        previews.grid(row=3, column=0, sticky="nsew")
        previews.grid_columnconfigure((0, 1), weight=1, uniform="preview")
        previews.grid_rowconfigure(0, weight=1)
        self.previews = []
        for i, title in enumerate(("ORIGINAL", "INVERTED")):
            card = ctk.CTkFrame(previews, fg_color=SURFACE, corner_radius=22)
            card.grid(row=0, column=i, sticky="nsew", padx=(0, 8) if i == 0 else (8, 0))
            self.label(card, title, 11, True, MUTED).pack(pady=(18, 10))
            view = self.label(card, "▤\n\nYour pages belong here" if i == 0 else "◐\n\nA softer late-night read", 16, color=MUTED)
            view.pack(expand=True, fill="both", padx=14, pady=(0, 18))
            self.previews.append(view)
        nav = ctk.CTkFrame(main, fg_color="transparent")
        nav.grid(row=4, column=0, pady=12)
        self.prev = ctk.CTkButton(nav, text="Prev", width=48, fg_color=SOFT, text_color=INK, command=lambda: self.navigate(-1))
        self.prev.pack(side="left")
        self.page_label = self.label(nav, "No document", 12, color=MUTED)
        self.page_label.pack(side="left", padx=18)
        self.next = ctk.CTkButton(nav, text="Next", width=48, fg_color=SOFT, text_color=INK, command=lambda: self.navigate(1))
        self.next.pack(side="left")
        bar = ctk.CTkFrame(main, fg_color=SURFACE, corner_radius=18)
        bar.grid(row=5, column=0, sticky="ew")
        self.label(bar, "Export quality", 12, True).pack(side="left", padx=(16, 10), pady=18)
        self.quality = ctk.CTkOptionMenu(bar, values=["96 DPI", "150 DPI", "200 DPI", "300 DPI"], width=110, fg_color=SOFT, text_color=INK, button_color=BLUE)
        self.quality.set("150 DPI")
        self.quality.pack(side="left")
        self.save_button = ctk.CTkButton(bar, text="↓  Invert & save PDF", height=42, corner_radius=14, fg_color="#188038", hover_color="#116529", command=self.save)
        self.save_button.pack(side="right", padx=14, pady=12)
        self.progress = ctk.CTkProgressBar(main, progress_color=BLUE, height=5)
        self.progress.grid(row=6, column=0, sticky="ew", pady=(14, 7))
        self.progress.set(0)
        self.status = self.label(main, "Ready. Your original file always stays untouched.", 12, color=MUTED)
        self.status.grid(row=7, column=0, sticky="w")
        self.label(main, "Exported pages are images; text selection and links are not retained.", 11, color=MUTED).grid(row=8, column=0, sticky="w", pady=(7, 0))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-o>", lambda e: self.open_file())
        self.controls()
        self.after(80, self.poll)

    def label(self, parent, text, size, bold=False, color=INK):
        return ctk.CTkLabel(parent, text=text, font=(self.family, size, "bold" if bold else "normal"), text_color=color, justify="left", wraplength=700)

    def controls(self):
        for widget in (self.open_button, self.clear_button, self.quality):
            widget.configure(state="disabled" if self.busy else "normal")
        self.save_button.configure(state="normal" if self.path and not self.busy else "disabled")
        self.prev.configure(state="normal" if self.path and self.page > 0 and not self.busy else "disabled")
        self.next.configure(state="normal" if self.path and self.page + 1 < self.pages and not self.busy else "disabled")

    def submit(self, kind, function, *args, **kwargs):
        self.busy = True
        self.controls()
        def run():
            try:
                self.events.put((kind, function(*args, **kwargs)))
            except Exception as exc:
                self.events.put(("error", str(exc)))
        self.pool.submit(run)

    def open_file(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(title="Open a PDF", filetypes=[("PDF documents", "*.pdf")])
        if path:
            self.pending_path = Path(path)
            self.pending_page = 0
            self.status.configure(text="Preparing your preview…")
            self.submit("preview", preview, path)

    def navigate(self, delta):
        if self.busy or not self.path:
            return
        self.pending_path = self.path
        self.pending_page = self.page + delta
        self.submit("preview", preview, self.path, self.pending_page)

    def save(self):
        if self.busy or not self.path:
            return
        target = filedialog.asksaveasfilename(title="Save inverted PDF", initialfile=self.path.stem + "-inverted.pdf", defaultextension=".pdf", filetypes=[("PDF documents", "*.pdf")])
        if not target:
            return
        self.cancel.clear()
        self.progress.set(0)
        self.status.configure(text="Inverting your pages…")
        self.submit("saved", invert_pdf, self.path, target, int(self.quality.get().split()[0]), progress=lambda done, total: self.events.put(("progress", (done, total))), cancel=self.cancel)

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "progress":
                    done, total = data
                    self.progress.set(done / total)
                    self.status.configure(text=f"Inverting page {done} of {total}…")
                    continue
                self.busy = False
                if kind == "preview":
                    original, inverted, self.pages = data
                    self.path, self.page = self.pending_path, self.pending_page
                    self.photos = []
                    for label, image in zip(self.previews, (original, inverted)):
                        image.thumbnail((290, 360))
                        photo = ctk.CTkImage(image, image, size=image.size)
                        label.configure(text="", image=photo)
                        self.photos.append(photo)
                    self.filename.configure(text=self.path.name)
                    self.page_label.configure(text=f"Page {self.page + 1} of {self.pages}")
                    self.status.configure(text="Preview ready. Save a copy whenever you're ready.")
                    self.progress.set(0)
                elif kind == "saved":
                    self.status.configure(text="Saved! Your inverted PDF is ready.")
                    self.progress.set(1)
                else:
                    self.status.configure(text="Couldn't complete that operation. You can try again.")
                    messagebox.showerror("Professor Reverse", data)
                self.controls()
        except Empty:
            pass
        self.after(80, self.poll)

    def clear(self):
        if self.busy:
            return
        self.path = None
        self.pages = self.page = 0
        for label in self.previews:
            label.configure(image=None, text="Open a PDF to preview")
        self.photos = []
        self.filename.configure(text="Open a PDF to get started")
        self.page_label.configure(text="No document")
        self.status.configure(text="Workspace cleared. Your files are unchanged.")
        self.progress.set(0)
        self.controls()

    def theme(self):
        self.dark = not self.dark
        ctk.set_appearance_mode("dark" if self.dark else "light")
        self.theme_button.configure(text="Light" if self.dark else "Dark")

    def close(self):
        if self.busy and not messagebox.askyesno("Close Professor Reverse?", "Stop after the current page and close? An unfinished export will not be saved."):
            return
        self.cancel.set()
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
