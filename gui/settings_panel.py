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
        
        # 4. Defaults
        self.add_section(content, self.tr["def_options"])
        self.type_var = ctk.StringVar(value=self.manager.get("default_type"))
        ctk.CTkOptionMenu(content, values=[self.tr["video"], self.tr["audio"]], variable=self.type_var, command=self.update_formats).pack(fill="x", padx=10, pady=5)

        self.format_var = ctk.StringVar(value=self.manager.get("default_format"))
        self.format_menu = ctk.CTkOptionMenu(content, values=["mp4", "mkv"], variable=self.format_var)
        self.format_menu.pack(fill="x", padx=10, pady=5)

        self.quality_var = ctk.StringVar(value=self.manager.get("default_quality"))
        self.quality_menu = ctk.CTkOptionMenu(content, values=["best", "1080p"], variable=self.quality_var)
        self.quality_menu.pack(fill="x", padx=10, pady=5)

        # 5. Open Folder
        self.open_folder_var = ctk.BooleanVar(value=self.manager.get("open_folder_after"))
        ctk.CTkCheckBox(content, text=self.tr["open_folder"], variable=self.open_folder_var).pack(pady=10, anchor="w", padx=10)

        # Save Button
        ctk.CTkButton(self, text=self.tr["save"], height=40, font=ctk.CTkFont(weight="bold"), command=self.save_settings).pack(pady=20, padx=20, fill="x")
        
        self.on_theme_change(self.theme_var.get())
        self.update_formats(self.type_var.get())

    def add_section(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(15,0))

    def on_theme_change(self, mode_display):
        # Check internal value
        internal = self.theme_map_rev.get(mode_display, "Dark")
        if internal == "System": 
            self.color_menu.pack_forget()
        else: 
            self.color_menu.pack(fill="x", padx=10, pady=5)

    def update_formats(self, choice):
        if choice == self.tr["audio"] or choice == "Audio":
            self.format_menu.configure(values=["mp3", "m4a", "wav"])
            self.quality_menu.configure(values=["320", "256", "192", "160", "128", "96", "64"])
            if self.quality_var.get() not in ["320", "256", "192", "160", "128", "96", "64"]: self.quality_var.set("192")
            if self.format_var.get() not in ["mp3", "m4a", "wav"]: self.format_var.set("mp3")
        else:
            self.format_menu.configure(values=["mp4", "mkv", "webm"])
            self.quality_menu.configure(values=["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"])
            if self.quality_var.get() not in ["best", "4320p (8K)", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p"]: self.quality_var.set("best")
            if self.format_var.get() not in ["mp4", "mkv", "webm"]: self.format_var.set("mp4")

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
        # Find key from display value
        new_color = "crimson_red"
        for k, v in self.tr["colors"].items():
            if v == new_color_display:
                new_color = k
                break
        
        new_lang = self.lang_var.get()
        default_type = "Audio" if self.type_var.get() == self.tr.get("audio") else "Video"

        self.manager.set("download_path", self.path_entry.get())
        self.manager.set("default_type", default_type)
        self.manager.set("default_format", self.format_var.get())
        self.manager.set("default_quality", self.quality_var.get())
        self.manager.set("open_folder_after", self.open_folder_var.get())
        self.manager.set("theme_mode", new_theme)
        self.manager.set("accent_color", new_color)
        self.manager.set("language", new_lang)
        
        self.parent.toggle_settings() # Close panel
        if old_theme != new_theme or old_color != new_color or old_lang != new_lang:
            self.reload_callback()
