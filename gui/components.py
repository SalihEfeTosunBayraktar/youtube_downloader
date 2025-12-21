import customtkinter as ctk
import threading
from PIL import Image
import urllib.request
import io
import os

class VideoItem(ctk.CTkFrame):
    def __init__(self, parent, info, settings_manager, remove_callback, tr, icon_path=None):
        super().__init__(parent)
        self.info = info
        self.settings = settings_manager
        self.remove_callback = remove_callback
        self.tr = tr
        self.icon_path = icon_path

        self.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self.thumb_label = ctk.CTkLabel(self, text="", width=80, height=60)
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=5, pady=5)
        
        # Async thumbnail loading to prevent UI freeze
        self.load_thumbnail(info.get('thumbnail'))

        # Title
        title = info.get('title', 'Unknown')
        if len(title) > 40: title = title[:37] + "..."
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=(5,0))

        # Options
        self.type_var = ctk.StringVar(value=self.settings.get("default_type"))
        
        # Localize display but keep valid internal values if possible, or mapping
        self.type_menu = ctk.CTkOptionMenu(self, values=[self.tr["video"], self.tr["audio"]], variable=self.type_var, width=80, height=20, font=("Arial", 10), command=self.update_options)
        self.type_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Need to set default visual to localized string
        if self.settings.get("default_type") == "Audio": self.type_var.set(self.tr["audio"])
        else: self.type_var.set(self.tr["video"])

        self.quality_var = ctk.StringVar(value=self.settings.get("default_quality"))
        self.quality_menu = ctk.CTkOptionMenu(self, values=["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"], variable=self.quality_var, width=80, height=20, font=("Arial", 10))
        self.quality_menu.grid(row=1, column=2, padx=5, pady=2, sticky="w")

        # Status / Remove
        self.status_label = ctk.CTkLabel(self, text=self.tr["queued"], text_color=("gray50", "gray80"), font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.grid(row=2, column=1, padx=5, pady=(0,5), sticky="w")

        self.remove_btn = ctk.CTkButton(self, text="X", width=30, height=20, fg_color="red", hover_color="darkred", command=lambda: self.remove_callback(self))
        self.remove_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ne")

        # Progress
        self.progress = ctk.CTkProgressBar(self, height=5)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=4, padx=5, pady=(0,5), sticky="ew")
        self.progress.grid_remove()

        self.update_options(self.type_var.get())

        # Restore default if needed
        self.quality_var.set(self.settings.get("default_quality"))


    def update_options(self, choice):
        if choice == self.tr["audio"]:
            self.quality_menu.configure(values=["320", "256", "192", "160", "128", "96", "64"])
            self.quality_var.set("192")
        else:
            self.quality_menu.configure(values=["mp4", "mkv", "webm"])
            self.quality_menu.configure(values=["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"])
            self.quality_var.set("best")

    def load_thumbnail(self, url):
        # Start a thread to download image
        threading.Thread(target=self._download_thumbnail_thread, args=(url,), daemon=True).start()

    def _download_thumbnail_thread(self, url):
        image = None
        try:
            if url:
                with urllib.request.urlopen(url) as u:
                    raw_data = u.read()
                image = Image.open(io.BytesIO(raw_data))
        except: 
            pass
            
        if image is None:
            # Fallback to app icon
            if self.icon_path and os.path.exists(self.icon_path):
                 try: image = Image.open(self.icon_path)
                 except: pass

        if image:
            # Resize
            image.thumbnail((80, 60))
            # Update UI on main thread
            self.after(0, self._update_thumbnail_ui, image)

    def _update_thumbnail_ui(self, image):
        try:
            if self.winfo_exists():
                ctk_image = ctk.CTkImage(image, size=image.size)
                self.thumb_label.configure(image=ctk_image)
        except Exception:
            pass

    def get_options(self):
        is_audio = self.type_var.get() == self.tr["audio"]
        ext_map = {self.tr["video"]: "mp4", self.tr["audio"]: "mp3"} 
        return {
            "format_type": "audio" if is_audio else "video",
            "quality": self.quality_var.get(),
            "ext": "mp3" if is_audio else "mp4",
            "is_playlist": self.info.get('is_playlist', False),
            "output_path": self.settings.get("download_path")
        }
