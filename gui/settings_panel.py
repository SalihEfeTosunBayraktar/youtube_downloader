import customtkinter as ctk
from tkinter import filedialog
from utils.locales import TRANSLATIONS

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent, manager, reload_callback):
        super().__init__(parent, corner_radius=0)
        self.manager = manager
        self.reload_callback = reload_callback
        self.parent = parent
        
        # Load data safely
        try:
            self.lang_code = self.manager.get("language")
            self.tr = TRANSLATIONS.get(self.lang_code, TRANSLATIONS["English"])
            
            # Map for themes
            self.theme_map = {
                "Dark": self.tr["dark"],
                "Light": self.tr["light"]
            }
            # Reverse map
            self.theme_map_rev = {v: k for k, v in self.theme_map.items()}

            self.build_ui()
        except Exception as e:
            ctk.CTkLabel(self, text=f"Error loading settings:\n{e}", text_color="red", wraplength=200).pack(pady=20)

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text=self.tr["settings_title"], font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="X", width=30, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=self.parent.toggle_settings).pack(side="right")
        
        # Content Scroll
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 1. Language
        self.add_section(content, self.tr["language"])
        self.lang_var = ctk.StringVar(value=self.lang_code)
        ctk.CTkOptionMenu(content, values=["English", "Turkish"], variable=self.lang_var).pack(fill="x", padx=10, pady=5)

        # 2. Download Path
        self.add_section(content, self.tr["download_loc"])
        path_frame = ctk.CTkFrame(content, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=5)
        
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, self.manager.get("download_path"))
        self.path_entry.configure(state="disabled")
        self.path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_frame, text="...", width=40, command=self.browse_path).pack(side="right", padx=(5,0))

        # 3. Appearance
        self.add_section(content, self.tr["appearance"])
        
        current_theme_internal = self.manager.get("theme_mode")
        current_theme_display = self.theme_map.get(current_theme_internal, current_theme_internal)
        
        self.theme_var = ctk.StringVar(value=current_theme_display)
        ctk.CTkOptionMenu(content, values=list(self.theme_map.values()), variable=self.theme_var, command=self.on_theme_change).pack(fill="x", padx=10, pady=5)

        # Color Container (Frame) - allows hiding content without losing position
        self.color_container = ctk.CTkFrame(content, fg_color="transparent")
        self.color_container.pack(fill="x")
        
        self.color_keys = list(self.tr["colors"].keys())
        self.color_display_values = [self.tr["colors"][k] for k in self.color_keys]
        
        saved_color_key = self.manager.get("accent_color")
        display_color = self.tr["colors"].get(saved_color_key, self.tr["colors"]["crimson_red"])
        
        self.color_var = ctk.StringVar(value=display_color)
        self.color_menu = ctk.CTkOptionMenu(self.color_container, values=self.color_display_values, variable=self.color_var)
        self.color_menu.pack(fill="x", padx=10, pady=5)
        
        # 4. Defaults Configuration
        self.add_section(content, self.tr.get("def_options", "Default Options"))
        
        # 4.1 Start Type
        ctk.CTkLabel(content, text=self.tr.get("def_start_type", "Start Type"), font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(5,0))
        self.add_type_var = ctk.StringVar(value=self.manager.get("default_add_type"))
        # Using localized values for display, mapping back on save
        self.type_display_map = {
            "Video": self.tr["video"],
            "Audio": self.tr["audio"],
            "Thumbnail": self.tr["thumbnail"]
        }
        self.type_value_map = {v: k for k, v in self.type_display_map.items()}
        
        current_add_type = self.manager.get("default_add_type")
        display_add_type = self.type_display_map.get(current_add_type, self.tr["video"])
        self.add_type_var.set(display_add_type)
        
        ctk.CTkOptionMenu(content, values=list(self.type_display_map.values()), variable=self.add_type_var).pack(fill="x", padx=20, pady=5)

        # 4.2 Video Defaults
        self.add_subsection(content, self.tr.get("def_video", "Video Defaults"))
        self.vid_fmt_var = ctk.StringVar(value=self.manager.get("video_format"))
        self.vid_qual_var = ctk.StringVar(value=self.manager.get("video_quality"))
        
        vf_frame = ctk.CTkFrame(content, fg_color="transparent")
        vf_frame.pack(fill="x", padx=20, pady=2)
        ctk.CTkOptionMenu(vf_frame, values=["mp4", "mkv", "webm"], variable=self.vid_fmt_var, width=100).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkOptionMenu(vf_frame, values=["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"], variable=self.vid_qual_var, width=100).pack(side="right", fill="x", expand=True, padx=(5,0))

        # 4.3 Audio Defaults
        self.add_subsection(content, self.tr.get("def_audio", "Audio Defaults"))
        self.aud_fmt_var = ctk.StringVar(value=self.manager.get("audio_format"))
        self.aud_qual_var = ctk.StringVar(value=self.manager.get("audio_quality"))
        
        af_frame = ctk.CTkFrame(content, fg_color="transparent")
        af_frame.pack(fill="x", padx=20, pady=2)
        ctk.CTkOptionMenu(af_frame, values=["mp3", "m4a", "wav"], variable=self.aud_fmt_var, width=100).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkOptionMenu(af_frame, values=["320", "256", "192", "160", "128", "96", "64"], variable=self.aud_qual_var, width=100).pack(side="right", fill="x", expand=True, padx=(5,0))

        # 4.4 Thumbnail Defaults
        self.add_subsection(content, self.tr.get("def_thumb", "Thumbnail Defaults"))
        self.thumb_fmt_var = ctk.StringVar(value=self.manager.get("thumb_format"))
        self.thumb_qual_var = ctk.StringVar(value=self.manager.get("thumb_quality"))

        tf_frame = ctk.CTkFrame(content, fg_color="transparent")
        tf_frame.pack(fill="x", padx=20, pady=2)
        ctk.CTkOptionMenu(tf_frame, values=["jpg", "png", "webp"], variable=self.thumb_fmt_var, width=100).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkOptionMenu(tf_frame, values=["Original", "1080p", "720p", "480p"], variable=self.thumb_qual_var, width=100).pack(side="right", fill="x", expand=True, padx=(5,0))

        # 5. Open Folder
        self.open_folder_var = ctk.BooleanVar(value=self.manager.get("open_folder_after"))
        ctk.CTkCheckBox(content, text=self.tr["open_folder"], variable=self.open_folder_var).pack(pady=20, anchor="w", padx=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkButton(btn_frame, text=self.tr["save"], height=40, font=ctk.CTkFont(weight="bold"), command=self.save_settings).pack(side="right", fill="x", expand=True, padx=(5,0))
        ctk.CTkButton(btn_frame, text=self.tr.get("reset_defaults", "Reset"), height=40, fg_color="gray", hover_color="gray30", command=self.reset_defaults).pack(side="left", fill="x", expand=True, padx=(0,5))
        
        self.on_theme_change(self.theme_var.get())

    def reset_defaults(self):
        # Reset UI vars to defaults defined in manager
        defaults = self.manager.defaults
        self.lang_var.set(defaults["language"])
        
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, defaults["download_path"])
        self.path_entry.configure(state="disabled")
        
        self.theme_var.set(self.theme_map.get(defaults["theme_mode"], defaults["theme_mode"]))
        self.color_var.set(self.tr["colors"].get(defaults["accent_color"], "Crimson Red"))
        
        # Reset new structure
        display_add = self.type_display_map.get(defaults["default_add_type"], self.tr["video"])
        self.add_type_var.set(display_add)
        
        self.vid_fmt_var.set(defaults["video_format"])
        self.vid_qual_var.set(defaults["video_quality"])
        self.aud_fmt_var.set(defaults["audio_format"])
        self.aud_qual_var.set(defaults["audio_quality"])
        self.thumb_fmt_var.set(defaults["thumb_format"])
        self.thumb_qual_var.set(defaults["thumb_quality"])
        
        self.open_folder_var.set(defaults["open_folder_after"])
        
        self.on_theme_change(self.theme_var.get())
        
        # Save and Reload immediately
        self.save_settings() 
        self.reload_callback()

    def add_section(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(15,0))

    def add_subsection(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10,0))
        
    def on_theme_change(self, mode_display):
        # Check internal value
        internal = self.theme_map_rev.get(mode_display, "Dark")
        if internal == "System": 
            self.color_menu.pack_forget()
        else: 
            self.color_menu.pack(fill="x", padx=10, pady=5)

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            self.path_entry.configure(state="disabled")

    def save_settings(self):
        old_theme, old_color, old_lang = self.manager.get("theme_mode"), self.manager.get("accent_color"), self.manager.get("language")
        
        new_theme_display = self.theme_var.get()
        new_theme = self.theme_map_rev.get(new_theme_display, "Dark")
        
        new_color_display = self.color_var.get()
        new_color = "crimson_red"
        for k, v in self.tr["colors"].items():
            if v == new_color_display:
                new_color = k
                break
        
        new_lang = self.lang_var.get()
        
        # Save Basic
        self.manager.set("download_path", self.path_entry.get())
        self.manager.set("open_folder_after", self.open_folder_var.get())
        self.manager.set("theme_mode", new_theme)
        self.manager.set("accent_color", new_color)
        self.manager.set("language", new_lang)
        
        # Save Advanced Defaults
        display_add_type = self.add_type_var.get()
        internal_add_type = self.type_value_map.get(display_add_type, "Video")
        self.manager.set("default_add_type", internal_add_type)
        
        self.manager.set("video_format", self.vid_fmt_var.get())
        self.manager.set("video_quality", self.vid_qual_var.get())
        self.manager.set("audio_format", self.aud_fmt_var.get())
        self.manager.set("audio_quality", self.aud_qual_var.get())
        self.manager.set("thumb_format", self.thumb_fmt_var.get())
        self.manager.set("thumb_quality", self.thumb_qual_var.get())
        
        self.parent.toggle_settings() # Close panel
        if old_theme != new_theme or old_color != new_color or old_lang != new_lang:
            self.reload_callback()
