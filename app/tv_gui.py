"""
Virtual TV Viewer GUI module.

Streams free-to-air HLS/MPEG-TS channels using python-vlc.
Requires VLC media player installed and python-vlc package.
"""
from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from backend.channels import (
    Channel,
    categories_for_channels,
    default_channels_file,
    filter_channel_indexes,
    load_channels,
    project_root,
    save_channels,
)

try:
    import vlc

    VLC_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover
    vlc = None
    VLC_IMPORT_ERROR = str(exc)


BG_COLOR = "#0f1b2d"
PANEL_COLOR = "#16263c"
VIDEO_BG = "#000000"
TITLE_COLOR = "#f4f6f8"
ACCENT_COLOR = "#f08a24"
ACCENT_SOFT = "#ffd3a8"
TEXT_COLOR = "#d7deea"
SOFT_BORDER = "#2a3d58"
SEL_BG = "#f08a24"
SEL_FG = "#10151f"


def _bundled_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parent.parent


def _preferred_channels_file() -> Path:
    return default_channels_file()


def _bundled_channels_file() -> Path:
    return _bundled_root() / "tv_channels.json"


def _preferred_icon_file() -> Path | None:
    candidates = [
        _project_root() / "assets" / "branding" / "adamsy-free-tv.ico",
        _bundled_root() / "assets" / "branding" / "adamsy-free-tv.ico",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _apply_window_icon(root: tk.Tk) -> None:
    icon_file = _preferred_icon_file()
    if not icon_file:
        return
    try:
        root.iconbitmap(default=str(icon_file))
    except Exception:
        pass


class TVPlayer:
    """Main GUI class for the Virtual TV Viewer."""

    def __init__(self, root: tk.Tk, channels_file: Path) -> None:
        self.root = root
        self.root.title("Adamsy Free TV - Live Channels")
        self.root.geometry("1120x680")
        self.root.minsize(900, 560)
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.channels_file = channels_file
        self.channels: list[Channel] = self._load_channels()
        self.filtered_indexes: list[int] = list(range(len(self.channels)))
        self.current_channel: Channel | None = None
        self._is_fullscreen = False

        self.instance = vlc.Instance("--no-xlib") if vlc else None
        self.player = self.instance.media_player_new() if self.instance else None

        self.status_var = tk.StringVar(value="Ready - select a channel and press Play.")
        self.np_var = tk.StringVar(value="Not playing")
        self.volume_var = tk.StringVar(value="Volume: 70%")
        self.search_var = tk.StringVar(value="")
        self.category_var = tk.StringVar(value="All")
        self.channel_count_var = tk.StringVar(value="0 channels")

        self._build_ui()
        self._refresh_filter_choices()
        self._populate_list()
        self._set_volume(70)

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=PANEL_COLOR)
        style.configure("Dark.TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR)
        style.configure("Accent.TButton", foreground="white", background=ACCENT_COLOR)
        style.configure("TButton", padding=7)
        style.configure("TCombobox", fieldbackground="#102033", background="#102033", foreground=TEXT_COLOR)
        style.configure("TScale", background=PANEL_COLOR)

        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=16, pady=(12, 0))

        tk.Label(
            header,
            text="Adamsy Free TV",
            font=("Segoe UI Variable Display", 24, "bold"),
            bg=BG_COLOR,
            fg=ACCENT_COLOR,
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="  Free-to-air live channels tuned for low-bandwidth viewing.",
            font=("Segoe UI", 10),
            bg=BG_COLOR,
            fg=ACCENT_SOFT,
        ).pack(side=tk.LEFT, pady=(8, 0))

        self.fs_button = tk.Button(
            header,
            text="Fullscreen",
            command=self._toggle_fullscreen,
            bg=PANEL_COLOR,
            fg=ACCENT_COLOR,
            activebackground="#223757",
            relief=tk.FLAT,
            padx=12,
            pady=7,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self.fs_button.pack(side=tk.RIGHT)

        body = tk.Frame(self.root, bg=BG_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=PANEL_COLOR, highlightbackground=SOFT_BORDER, highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), ipadx=4)
        left.pack_propagate(False)
        left.config(width=320)

        tk.Label(
            left,
            text="Channel Library",
            font=("Segoe UI Variable Display", 13, "bold"),
            bg=PANEL_COLOR,
            fg=TITLE_COLOR,
        ).pack(anchor=tk.W, padx=10, pady=(10, 4))
        tk.Label(
            left,
            textvariable=self.channel_count_var,
            font=("Segoe UI", 9),
            bg=PANEL_COLOR,
            fg=ACCENT_SOFT,
        ).pack(anchor=tk.W, padx=10, pady=(0, 4))

        srch = tk.Frame(left, bg=PANEL_COLOR)
        srch.pack(fill=tk.X, padx=10)
        tk.Label(srch, text="Search", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(srch, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self.search_var.trace_add("write", self._on_search_changed)

        filter_row = tk.Frame(left, bg=PANEL_COLOR)
        filter_row.pack(fill=tk.X, padx=10, pady=(6, 0))
        tk.Label(filter_row, text="Category", bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(
            filter_row,
            textvariable=self.category_var,
            values=["All"],
            state="readonly",
            width=22,
        )
        self.category_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_changed)

        self.ch_listbox = tk.Listbox(
            left,
            activestyle="none",
            bg="#181818",
            fg=TEXT_COLOR,
            selectbackground=SEL_BG,
            selectforeground=SEL_FG,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 10),
            height=20,
        )
        self.ch_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.ch_listbox.bind("<<ListboxSelect>>", self._on_channel_select)
        self.ch_listbox.bind("<Double-Button-1>", lambda _event: self.play_selected())

        btn_row = tk.Frame(left, bg=PANEL_COLOR)
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.play_btn = ttk.Button(btn_row, text="Play", command=self.play_selected)
        self.play_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btn_row, text="Stop", command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.prev_btn = ttk.Button(btn_row, text="Prev", command=self.play_previous)
        self.prev_btn.pack(side=tk.LEFT, padx=(6, 0))
        self.next_btn = ttk.Button(btn_row, text="Next", command=self.play_next)
        self.next_btn.pack(side=tk.LEFT, padx=(6, 0))

        add_row = tk.Frame(left, bg=PANEL_COLOR)
        add_row.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Button(add_row, text="+ Add Channel", command=self._add_channel_dialog).pack(side=tk.LEFT)
        ttk.Button(add_row, text="Remove", command=self._remove_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(add_row, text="Refresh Channels", command=self._update_channel_list).pack(side=tk.LEFT, padx=(6, 0))

        right = tk.Frame(body, bg=BG_COLOR)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.video_frame = tk.Frame(right, bg=VIDEO_BG, highlightbackground=SOFT_BORDER, highlightthickness=1)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        self.video_canvas = tk.Canvas(self.video_frame, bg=VIDEO_BG, highlightthickness=0)
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        self.video_canvas.bind("<Double-Button-1>", lambda _event: self._toggle_fullscreen())
        self.video_canvas.after(100, self._draw_placeholder)

        info = tk.Frame(right, bg=PANEL_COLOR, highlightbackground=SOFT_BORDER, highlightthickness=1)
        info.pack(fill=tk.X, pady=(8, 0))

        tk.Label(
            info,
            textvariable=self.np_var,
            font=("Segoe UI Variable Display", 11, "bold"),
            bg=PANEL_COLOR,
            fg=ACCENT_COLOR,
        ).pack(side=tk.LEFT, padx=12, pady=6)
        tk.Label(
            info,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
        ).pack(side=tk.LEFT, padx=(0, 12))

        vol_frame = tk.Frame(info, bg=PANEL_COLOR)
        vol_frame.pack(side=tk.RIGHT, padx=12)
        tk.Label(vol_frame, textvariable=self.volume_var, bg=PANEL_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.vol_slider = ttk.Scale(
            vol_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_volume_change,
            length=120,
        )
        self.vol_slider.pack(side=tk.LEFT, padx=(6, 0))

    def _draw_placeholder(self) -> None:
        width = self.video_canvas.winfo_width() or 640
        height = self.video_canvas.winfo_height() or 360
        self.video_canvas.create_rectangle(0, 0, width, height, fill=VIDEO_BG, outline="")
        self.video_canvas.create_text(
            width // 2,
            height // 2,
            text="[TV] Select a channel and press Play",
            fill="#444444",
            font=("Bahnschrift", 16),
            anchor=tk.CENTER,
        )

    def _load_channels(self) -> list[Channel]:
        return load_channels(self.channels_file, fallback_file=_bundled_channels_file())

    def _save_channels(self) -> None:
        save_channels(self.channels_file, self.channels)

    def _refresh_filter_choices(self) -> None:
        categories = categories_for_channels(self.channels)
        self.category_combo["values"] = ["All", *categories]
        if self.category_var.get() not in self.category_combo["values"]:
            self.category_var.set("All")

    def _populate_list(self, query: str = "") -> None:
        self.filtered_indexes = filter_channel_indexes(
            self.channels,
            query=query,
            category=self.category_var.get(),
        )

        self.ch_listbox.delete(0, tk.END)
        for index in self.filtered_indexes:
            channel = self.channels[index]
            label = channel.name + (f"  [{channel.country}]" if channel.country else "")
            self.ch_listbox.insert(tk.END, label)
        self.channel_count_var.set(f"{len(self.filtered_indexes):,} visible / {len(self.channels):,} total")

    def _on_search_changed(self, *_args: object) -> None:
        self._populate_list(self.search_var.get())

    def _on_category_changed(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self._populate_list(self.search_var.get())

    def _on_channel_select(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        selection = self.ch_listbox.curselection()
        if not selection:
            return
        real_index = self.filtered_indexes[selection[0]]
        self.current_channel = self.channels[real_index]

    def _attach_vlc_to_canvas(self) -> None:
        if not self.player:
            return
        window_id = self.video_canvas.winfo_id()
        if sys.platform.startswith("win"):
            self.player.set_hwnd(window_id)
        elif sys.platform == "darwin":
            self.player.set_nsobject(window_id)
        else:
            self.player.set_xwindow(window_id)

    def play_selected(self) -> None:
        if not vlc:
            messagebox.showerror(
                "VLC Not Available",
                f"python-vlc is required.\n\nInstall it with:\n  pip install python-vlc\n\nDetails: {VLC_IMPORT_ERROR}",
            )
            return
        if not self.current_channel:
            selection = self.ch_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Channel", "Please select a channel first.")
                return
            real_index = self.filtered_indexes[selection[0]]
            self.current_channel = self.channels[real_index]

        channel = self.current_channel
        self.status_var.set(f"Connecting to {channel.name}...")
        self.np_var.set(f"Now Playing: {channel.name}")
        self.root.update_idletasks()

        media = self.instance.media_new(channel.url)
        media.add_option(":network-caching=3000")
        media.add_option(":adaptive-maxheight=480")
        self.player.set_media(media)
        self._attach_vlc_to_canvas()
        self.player.play()

        self.status_var.set(f"Streaming: {channel.name}  |  {channel.country}  |  {channel.category}")

    def stop(self) -> None:
        if self.player:
            self.player.stop()
        self.status_var.set("Stopped.")
        self.np_var.set("Not playing")
        self._draw_placeholder()

    def play_previous(self) -> None:
        self._step_channel(-1)

    def play_next(self) -> None:
        self._step_channel(1)

    def _step_channel(self, delta: int) -> None:
        if not self.filtered_indexes:
            return
        selection = self.ch_listbox.curselection()
        current_pos = selection[0] if selection else -1
        new_pos = (current_pos + delta) % len(self.filtered_indexes)
        self.ch_listbox.selection_clear(0, tk.END)
        self.ch_listbox.selection_set(new_pos)
        self.ch_listbox.see(new_pos)
        real_index = self.filtered_indexes[new_pos]
        self.current_channel = self.channels[real_index]
        self.play_selected()

    def _set_volume(self, value: int) -> None:
        if self.player:
            self.player.audio_set_volume(int(value))
        self.vol_slider.set(value)
        self.volume_var.set(f"Volume: {int(value)}%")

    def _on_volume_change(self, value: str) -> None:
        volume = int(float(value))
        if self.player:
            self.player.audio_set_volume(volume)
        self.volume_var.set(f"Volume: {volume}%")

    def _toggle_fullscreen(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)
        self.fs_button.config(text="Exit Fullscreen" if self._is_fullscreen else "Fullscreen")
        if self.player and self.player.is_playing():
            self.root.after(200, self._attach_vlc_to_canvas)

    def _add_channel_dialog(self) -> None:
        name = simpledialog.askstring("Add Channel", "Channel name:", parent=self.root)
        if not name or not name.strip():
            return
        url = simpledialog.askstring("Add Channel", "Stream URL (HLS/M3U8/RTMP):", parent=self.root)
        if not url or not url.strip():
            return
        country = simpledialog.askstring("Add Channel", "Country (optional):", parent=self.root) or ""
        category = simpledialog.askstring("Add Channel", "Category (optional):", parent=self.root) or ""
        channel = Channel(name=name.strip(), url=url.strip(), country=country.strip(), category=category.strip())
        self.channels.append(channel)
        self._save_channels()
        self._refresh_filter_choices()
        self._populate_list(self.search_var.get())

    def _remove_selected(self) -> None:
        selection = self.ch_listbox.curselection()
        if not selection:
            messagebox.showinfo("Nothing selected", "Select a channel to remove.")
            return
        real_index = self.filtered_indexes[selection[0]]
        channel = self.channels[real_index]
        if not messagebox.askyesno("Remove Channel", f"Remove '{channel.name}'?"):
            return
        if self.current_channel and self.current_channel is channel:
            self.stop()
            self.current_channel = None
        self.channels.pop(real_index)
        self._save_channels()
        self._refresh_filter_choices()
        self._populate_list(self.search_var.get())

    def _on_close(self) -> None:
        if self.player:
            self.player.stop()
            self.player.release()
        if self.instance:
            self.instance.release()
        self.root.destroy()

    def _update_channel_list(self) -> None:
        if not messagebox.askyesno(
            "Update Channel List",
            "This will download 700+ free-to-air channels from iptv-org\n"
            "and replace the current channel list.\n\nRequires internet. Continue?",
            parent=self.root,
        ):
            return

        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating...")
        progress_window.geometry("360x110")
        progress_window.resizable(False, False)
        progress_window.grab_set()
        tk.Label(
            progress_window,
            text="Fetching channel list from iptv-org...",
            font=("Candara", 11),
            pady=12,
        ).pack()
        progress_bar = ttk.Progressbar(progress_window, mode="indeterminate", length=300)
        progress_bar.pack(pady=4)
        progress_bar.start(12)
        status_label = tk.Label(progress_window, text="Connecting...", font=("Candara", 9), fg="#555555")
        status_label.pack(pady=4)

        def _worker() -> None:
            try:
                import tv_updater

                self.root.after(0, lambda: status_label.config(text="Parsing channels..."))
                tv_updater.main(
                    [
                        "--limit",
                        "700",
                        "--verify-live",
                        "--verify-count",
                        "2000",
                        "--output",
                        str(self.channels_file),
                    ]
                )
                self.root.after(0, _done)
            except Exception as exc:
                self.root.after(0, lambda error=exc: _error(error))

        def _done() -> None:
            progress_window.destroy()
            self.channels = self._load_channels()
            self._refresh_filter_choices()
            self._populate_list()
            messagebox.showinfo(
                "Done",
                f"Channel list updated - {len(self.channels):,} channels loaded.",
                parent=self.root,
            )

        def _error(exc: Exception) -> None:
            progress_window.destroy()
            messagebox.showerror("Update Failed", f"Could not update channels:\n{exc}", parent=self.root)

        threading.Thread(target=_worker, daemon=True).start()


def launch_tv_gui(channels_file: Path | None = None) -> None:
    if channels_file is None:
        channels_file = _preferred_channels_file()

    root = tk.Tk()
    _apply_window_icon(root)
    TVPlayer(root, channels_file)
    root.mainloop()
