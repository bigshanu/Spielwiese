import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from downloader import (
    download_video,
    get_video_info,
    get_default_download_path,
    format_duration,
)

APP_TITLE = "YouTube Downloader"
WINDOW_WIDTH = 620
WINDOW_HEIGHT = 480
BG_COLOR = "#1a1a2e"
ACCENT_COLOR = "#e94560"
CARD_COLOR = "#16213e"
TEXT_COLOR = "#eaeaea"
MUTED_COLOR = "#888"
ENTRY_BG = "#0f3460"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self._download_path = get_default_download_path()
        self._is_downloading = False

        self._build_ui()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        # Title
        tk.Label(
            self,
            text="YouTube Downloader",
            font=("SF Pro Display", 22, "bold"),
            bg=BG_COLOR,
            fg=ACCENT_COLOR,
        ).pack(pady=(28, 4))

        tk.Label(
            self,
            text="Videos & Musik bequem herunterladen",
            font=("SF Pro Display", 11),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
        ).pack(pady=(0, 18))

        # Card frame
        card = tk.Frame(self, bg=CARD_COLOR, bd=0)
        card.pack(padx=30, fill="x")

        # URL input
        self._add_label(card, "YouTube-URL")
        url_row = tk.Frame(card, bg=CARD_COLOR)
        url_row.pack(fill="x", padx=16, pady=(0, 12))

        self._url_var = tk.StringVar()
        url_entry = tk.Entry(
            url_row,
            textvariable=self._url_var,
            font=("SF Pro Display", 12),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=6,
        )
        url_entry.pack(side="left", fill="x", expand=True)
        url_entry.bind("<Return>", lambda _: self._fetch_info())

        tk.Button(
            url_row,
            text="Info",
            font=("SF Pro Display", 11),
            bg=ACCENT_COLOR,
            fg="white",
            relief="flat",
            padx=10,
            cursor="hand2",
            command=self._fetch_info,
        ).pack(side="left", padx=(6, 0))

        # Info label
        self._info_var = tk.StringVar(value="")
        tk.Label(
            card,
            textvariable=self._info_var,
            font=("SF Pro Display", 10),
            bg=CARD_COLOR,
            fg=MUTED_COLOR,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 10))

        # Format + Quality row
        opts_row = tk.Frame(card, bg=CARD_COLOR)
        opts_row.pack(fill="x", padx=16, pady=(0, 12))

        self._add_label(card, "Format & Qualität", padx=16)
        fmt_row = tk.Frame(card, bg=CARD_COLOR)
        fmt_row.pack(fill="x", padx=16, pady=(0, 14))

        self._format_var = tk.StringVar(value="mp4")
        for fmt in ("mp4", "mp3"):
            tk.Radiobutton(
                fmt_row,
                text=fmt.upper(),
                variable=self._format_var,
                value=fmt,
                font=("SF Pro Display", 11),
                bg=CARD_COLOR,
                fg=TEXT_COLOR,
                selectcolor=ENTRY_BG,
                activebackground=CARD_COLOR,
                command=self._on_format_change,
            ).pack(side="left", padx=(0, 14))

        self._quality_var = tk.StringVar(value="best")
        self._quality_combo = ttk.Combobox(
            fmt_row,
            textvariable=self._quality_var,
            values=["best", "1080p", "720p", "480p"],
            state="readonly",
            width=10,
            font=("SF Pro Display", 11),
        )
        self._quality_combo.pack(side="left")

        # Download path
        self._add_label(card, "Speicherort", padx=16)
        path_row = tk.Frame(card, bg=CARD_COLOR)
        path_row.pack(fill="x", padx=16, pady=(0, 16))

        self._path_var = tk.StringVar(value=self._download_path)
        tk.Entry(
            path_row,
            textvariable=self._path_var,
            font=("SF Pro Display", 11),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=6,
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            path_row,
            text="...",
            font=("SF Pro Display", 11),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            relief="flat",
            padx=8,
            cursor="hand2",
            command=self._choose_path,
        ).pack(side="left", padx=(6, 0))

        # Progress
        self._progress_var = tk.DoubleVar()
        self._progress_label = tk.StringVar(value="")
        tk.Label(
            self,
            textvariable=self._progress_label,
            font=("SF Pro Display", 10),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
        ).pack(pady=(14, 2))

        self._progress_bar = ttk.Progressbar(
            self, variable=self._progress_var, maximum=100, length=WINDOW_WIDTH - 60
        )
        self._progress_bar.pack(pady=(0, 10))

        # Download button
        self._dl_btn = tk.Button(
            self,
            text="Download starten",
            font=("SF Pro Display", 13, "bold"),
            bg=ACCENT_COLOR,
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._start_download,
        )
        self._dl_btn.pack(pady=(4, 0))

        # Open folder
        tk.Button(
            self,
            text="Ordner öffnen",
            font=("SF Pro Display", 11),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
            relief="flat",
            cursor="hand2",
            command=self._open_folder,
        ).pack(pady=(6, 0))

    # --------------------------------------------------------------- helpers -

    def _add_label(self, parent, text, padx=16):
        tk.Label(
            parent,
            text=text,
            font=("SF Pro Display", 10, "bold"),
            bg=CARD_COLOR,
            fg=MUTED_COLOR,
            anchor="w",
        ).pack(fill="x", padx=padx, pady=(10, 2))

    def _on_format_change(self):
        if self._format_var.get() == "mp3":
            self._quality_combo.config(state="disabled")
        else:
            self._quality_combo.config(state="readonly")

    def _choose_path(self):
        path = filedialog.askdirectory(initialdir=self._path_var.get())
        if path:
            self._path_var.set(path)

    def _open_folder(self):
        path = self._path_var.get()
        if os.path.exists(path):
            os.system(f'open "{path}"')
        else:
            messagebox.showinfo("Info", f"Ordner existiert noch nicht:\n{path}")

    def _fetch_info(self):
        url = self._url_var.get().strip()
        if not url:
            return
        self._info_var.set("Lade Info...")

        def fetch():
            try:
                info = get_video_info(url)
                duration_str = format_duration(info["duration"])
                self._info_var.set(
                    f"{info['title']}  •  {duration_str}  •  {info['uploader']}"
                )
            except Exception as e:
                self._info_var.set(f"Fehler: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    # ------------------------------------------------------------ download ---

    def _start_download(self):
        if self._is_downloading:
            return

        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Fehlende URL", "Bitte eine YouTube-URL eingeben.")
            return

        self._is_downloading = True
        self._dl_btn.config(state="disabled", text="Lädt herunter…")
        self._progress_var.set(0)

        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                if total:
                    pct = downloaded / total * 100
                    self._progress_var.set(pct)
                label = f"{speed}  –  ETA {eta}" if speed else ""
                self._progress_label.set(label)
            elif d["status"] == "finished":
                self._progress_var.set(100)
                self._progress_label.set("Verarbeite…")

        def run():
            try:
                download_video(
                    url=url,
                    download_path=self._path_var.get(),
                    format_choice=self._format_var.get(),
                    quality=self._quality_var.get(),
                    progress_hook=hook,
                )
                self._progress_label.set("Fertig!")
                messagebox.showinfo("Fertig", "Download abgeschlossen!")
            except Exception as e:
                self._progress_label.set("")
                messagebox.showerror("Fehler", str(e))
            finally:
                self._is_downloading = False
                self._dl_btn.config(state="normal", text="Download starten")

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
