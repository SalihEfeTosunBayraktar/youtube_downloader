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
        # Load initial type
        # "default_add_type" is the mode new items start in.
        start_type = self.settings.get("default_add_type")
        self.type_var = ctk.StringVar(value=start_type)
        
        # Localize display but keep valid internal values if possible, or mapping
        self.type_menu = ctk.CTkOptionMenu(self, values=[self.tr["video"], self.tr["audio"], self.tr["thumbnail"]], variable=self.type_var, width=80, height=20, font=("Arial", 10), command=self.update_options)
        self.type_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Set localized string
        if start_type == "Audio": self.type_var.set(self.tr["audio"])
        elif start_type == "Thumbnail": self.type_var.set(self.tr["thumbnail"])
        else: self.type_var.set(self.tr["video"])

        self.quality_var = ctk.StringVar()
        self.quality_menu = ctk.CTkOptionMenu(self, values=[], variable=self.quality_var, width=80, height=20, font=("Arial", 10))
        self.quality_menu.grid(row=1, column=2, padx=5, pady=2, sticky="w")

        # Format Menu (New)
        self.format_var = ctk.StringVar()
        self.format_menu = ctk.CTkOptionMenu(self, values=[], variable=self.format_var, width=70, height=20, font=("Arial", 10))
        self.format_menu.grid(row=1, column=3, padx=5, pady=2, sticky="w")

        # Status / Remove
        self.status_label = ctk.CTkLabel(self, text=self.tr["queued"], text_color=("gray50", "gray80"), font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.grid(row=2, column=1, columnspan=3, padx=5, pady=(0,5), sticky="w") # Spanned to cover new col

        self.remove_btn = ctk.CTkButton(self, text="X", width=30, height=20, fg_color="red", hover_color="darkred", command=lambda: self.remove_callback(self))
        self.remove_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ne")

        # Progress
        self.progress = ctk.CTkProgressBar(self, height=5)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=5, padx=5, pady=(0,5), sticky="ew")
        self.progress.grid_remove()

        # Initialize options based on current type
        self.update_options(self.type_var.get(), initial=True)


    def update_options(self, choice, initial=False):
        # Determine defaults key prefix based on choice
        # Choice is localized string
        
        target_mode = "video"
        if choice == self.tr["audio"]: target_mode = "audio"
        elif choice == self.tr["thumbnail"]: target_mode = "thumb"
        
        # Configure menus
        if target_mode == "audio":
            self.quality_menu.configure(values=["320", "256", "192", "160", "128", "96", "64"])
            self.format_menu.configure(values=["mp3", "m4a", "wav"])
        elif target_mode == "thumb":
             self.quality_menu.configure(values=["Original", "1080p", "720p", "480p"])
             self.format_menu.configure(values=["jpg", "png", "webp"])
        else: # video
            self.quality_menu.configure(values=["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"])
            self.format_menu.configure(values=["mp4", "mkv", "webm"])
            
        # Set values
        # If initial=True, load from settings defaults specifically for this mode
        # If not initial (user passed choice), we could also load defaults for that mode?
        # Yes, user expects "If I switch to Audio, give me Audio defaults"
        
        def_fmt = self.settings.get(f"{target_mode}_format")
        def_qual = self.settings.get(f"{target_mode}_quality")
        
        # Set them
        self.format_var.set(def_fmt)
        self.quality_var.set(def_qual)

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
        choice = self.type_var.get()
        is_audio = choice == self.tr["audio"]
        is_thumbnail = choice == self.tr["thumbnail"]
        
        format_type = "video"
        if is_audio: format_type = "audio"
        if is_thumbnail: format_type = "thumbnail"
        
        return {
            "format_type": format_type,
            "quality": self.quality_var.get(),
            "ext": self.format_var.get(),
            "is_playlist": self.info.get('is_playlist', False),
            "output_path": self.settings.get("download_path")
        }
