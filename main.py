import customtkinter as ctk
import threading
from PIL import Image
import urllib.request
import io
import os
import json
import subprocess
import sys
from tkinter import filedialog
from downloader import YoutubeDownloader
import winreg


# Determine paths
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(application_path, "app_icon.ico")


# Localization Dictionary
TRANSLATIONS = {
    "English": {
        "title": "Modern YouTube Downloader by Legendnoobe",
        "settings_title": "Application Settings",
        "download_loc": "Download Location",
        "browse": "Browse",
        "appearance": "Appearance",
        "theme_label": "Theme",
        "accent_label": "Accent Color",
        "restart_hint": "* Restart required for accent color",
        "def_options": "Default Download Options",
        "open_folder": "Open folder after download",
        "save": "Save Settings",
        "created_by": "Created by legendnoobe",
        "paste_link": "Paste Link...",
        "queue_label": "Download Queue",
        "start_all": "Start Download All",
        "downloading": "Downloading...",
        "completed": "Completed",
        "failed": "Failed",
        "queued": "Queued",
        "language": "Language",
        "video": "Video",
        "audio": "Audio",
        "dark": "Dark",
        "light": "Light",
        "colors": {
            "crimson_red": "Crimson Red", "coral_red": "Coral Red", "deep_orange": "Deep Orange", 
            "golden_orange": "Golden Orange", "amber_yellow": "Amber Yellow", "cyber_yellow": "Cyber Yellow",
            "lime_green": "Lime Green", "neon_green": "Neon Green", "mint_green": "Mint Green", "emerald_green": "Emerald Green",
            "turquoise_glow": "Turquoise Glow", "neon_cyan": "Neon Cyan", "teal": "Teal",
            "electric_blue": "Electric Blue", "ocean_blue": "Ocean Blue", "steel_blue": "Steel Blue", 
            "indigo_blue": "Indigo Blue", "midnight_blue": "Midnight Blue",
            "royal_purple": "Royal Purple", "violet_glow": "Violet Glow", "magenta": "Magenta",
            "hot_pink": "Hot Pink", "rose_pink": "Rose Pink", "slate_gray": "Slate Gray"
        }
    },
    "Turkish": {
        "title": "Modern YouTube İndirici by Legendnoobe",
        "settings_title": "Uygulama Ayarları",
        "download_loc": "İndirme Konumu",
        "browse": "Gözat",
        "appearance": "Görünüm",
        "theme_label": "Tema",
        "accent_label": "Vurgu Rengi",
        "restart_hint": "* Vurgu rengi için yeniden başlatma gerekir",
        "def_options": "Varsayılan İndirme Seçenekleri",
        "open_folder": "İndirdikten sonra klasörü aç",
        "save": "Ayarları Kaydet",
        "created_by": "legendnoobe tarafından oluşturuldu",
        "paste_link": "Bağlantıyı Yapıştır...",
        "queue_label": "İndirme Kuyruğu",
        "start_all": "Tümünü İndir",
        "downloading": "İndiriliyor...",
        "completed": "Tamamlandı",
        "failed": "Başarısız",
        "queued": "Kuyrukta",
        "language": "Dil",
        "video": "Video",
        "audio": "Ses",
        "dark": "Koyu",
        "light": "Açık",
        "colors": {
            "crimson_red": "Kızıl Kırmızı", "coral_red": "Mercan Kırmızısı", "deep_orange": "Koyu Turuncu",
            "golden_orange": "Altın Turuncu", "amber_yellow": "Kehribar Sarısı", "cyber_yellow": "Siber Sarı",
            "lime_green": "Limon Yeşili", "neon_green": "Neon Yeşil", "mint_green": "Nane Yeşili", "emerald_green": "Zümrüt Yeşili",
            "turquoise_glow": "Turkuaz Parıltısı", "neon_cyan": "Neon Camgöbeği", "teal": "Çamurcun",
            "electric_blue": "Elektrik Mavisi", "ocean_blue": "Okyanus Mavisi", "steel_blue": "Çelik Mavisi",
            "indigo_blue": "Çivit Mavisi", "midnight_blue": "Gece Mavisi",
            "royal_purple": "Kraliyet Moru", "violet_glow": "Menekşe Parıltısı", "magenta": "Eflatun",
            "hot_pink": "Sıcak Pembe", "rose_pink": "Gül Pembesi", "slate_gray": "Arduvaz Grisi"
        }
    }
}

class SettingsManager:
    def __init__(self):
        # Determine AppData path
        appdata = os.getenv('APPDATA')
        if not appdata: appdata = os.path.expanduser("~")
        
        self.config_dir = os.path.join(appdata, "ModernYoutubeDownloader")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.filename = os.path.join(self.config_dir, "settings.json")
        
        self.defaults = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "default_type": "Video", # Video, Audio
            "default_format": "mp4", # mp4, mkv / mp3
            "default_quality": "best",
            "open_folder_after": True,
            "theme_mode": "Dark", # System, Dark, Light
            "accent_color": "crimson_red", 
            "language": "English"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filename):
            data = self.defaults.copy()
        else:
            try:
                with open(self.filename, 'r') as f:
                    data = {**self.defaults, **json.load(f)}
            except:
                data = self.defaults.copy()
        
        ac = data.get("accent_color", "")
        if ac == "red": data["accent_color"] = "crimson_red"
        elif ac == "orange": data["accent_color"] = "golden_orange"
        
        return data

    def save_settings(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

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
            
            # Map for themes - REMOVED SYSTEM
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
        if current_theme_internal == "System": current_theme_internal = "Dark" # Fallback if migrating user data
        
        current_theme_display = self.theme_map.get(current_theme_internal, current_theme_internal)
        
        self.theme_var = ctk.StringVar(value=current_theme_display)
        ctk.CTkOptionMenu(content, values=list(self.theme_map.values()), variable=self.theme_var).pack(fill="x", padx=10, pady=5)

        # Color Container (Frame) 
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
        
        self.update_formats(self.type_var.get())

    def add_section(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(15,0))

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



# Localization Dictionary
TRANSLATIONS = {
    "English": {
        "title": "Modern YouTube Downloader by Legendnoobe",
        "settings_title": "Application Settings",
        "download_loc": "Download Location",
        "browse": "Browse",
        "appearance": "Appearance",
        "theme_label": "Theme",
        "accent_label": "Accent Color",
        "restart_hint": "* Restart required for accent color",
        "def_options": "Default Download Options",
        "open_folder": "Open folder after download",
        "save": "Save Settings",
        "created_by": "Created by legendnoobe",
        "paste_link": "Paste Link...",
        "queue_label": "Download Queue",
        "start_all": "Start Download All",
        "downloading": "Downloading...",
        "completed": "Completed",
        "failed": "Failed",
        "queued": "Queued",
        "language": "Language",
        "video": "Video",
        "audio": "Audio",
        "dark": "Dark",
        "light": "Light",
        "colors": {
            "crimson_red": "Crimson Red", "coral_red": "Coral Red", "deep_orange": "Deep Orange", 
            "golden_orange": "Golden Orange", "amber_yellow": "Amber Yellow", "cyber_yellow": "Cyber Yellow",
            "lime_green": "Lime Green", "neon_green": "Neon Green", "mint_green": "Mint Green", "emerald_green": "Emerald Green",
            "turquoise_glow": "Turquoise Glow", "neon_cyan": "Neon Cyan", "teal": "Teal",
            "electric_blue": "Electric Blue", "ocean_blue": "Ocean Blue", "steel_blue": "Steel Blue", 
            "indigo_blue": "Indigo Blue", "midnight_blue": "Midnight Blue",
            "royal_purple": "Royal Purple", "violet_glow": "Violet Glow", "magenta": "Magenta",
            "hot_pink": "Hot Pink", "rose_pink": "Rose Pink", "slate_gray": "Slate Gray"
        }
    },
    "Turkish": {
        "title": "Modern YouTube İndirici by Legendnoobe",
        "settings_title": "Uygulama Ayarları",
        "download_loc": "İndirme Konumu",
        "browse": "Gözat",
        "appearance": "Görünüm",
        "theme_label": "Tema",
        "accent_label": "Vurgu Rengi",
        "restart_hint": "* Vurgu rengi için yeniden başlatma gerekir",
        "def_options": "Varsayılan İndirme Seçenekleri",
        "open_folder": "İndirdikten sonra klasörü aç",
        "save": "Ayarları Kaydet",
        "created_by": "legendnoobe tarafından oluşturuldu",
        "paste_link": "Bağlantıyı Yapıştır...",
        "queue_label": "İndirme Kuyruğu",
        "start_all": "Tümünü İndir",
        "downloading": "İndiriliyor...",
        "completed": "Tamamlandı",
        "failed": "Başarısız",
        "queued": "Kuyrukta",
        "language": "Dil",
        "video": "Video",
        "audio": "Ses",
        "dark": "Koyu",
        "light": "Açık",
        "colors": {
            "crimson_red": "Kızıl Kırmızı", "coral_red": "Mercan Kırmızısı", "deep_orange": "Koyu Turuncu",
            "golden_orange": "Altın Turuncu", "amber_yellow": "Kehribar Sarısı", "cyber_yellow": "Siber Sarı",
            "lime_green": "Limon Yeşili", "neon_green": "Neon Yeşil", "mint_green": "Nane Yeşili", "emerald_green": "Zümrüt Yeşili",
            "turquoise_glow": "Turkuaz Parıltısı", "neon_cyan": "Neon Camgöbeği", "teal": "Çamurcun",
            "electric_blue": "Elektrik Mavisi", "ocean_blue": "Okyanus Mavisi", "steel_blue": "Çelik Mavisi",
            "indigo_blue": "Çivit Mavisi", "midnight_blue": "Gece Mavisi",
            "royal_purple": "Kraliyet Moru", "violet_glow": "Menekşe Parıltısı", "magenta": "Eflatun",
            "hot_pink": "Sıcak Pembe", "rose_pink": "Gül Pembesi", "slate_gray": "Arduvaz Grisi"
        }
    }
}

class SettingsManager:
    def __init__(self):
        # Determine AppData path
        appdata = os.getenv('APPDATA')
        if not appdata: appdata = os.path.expanduser("~")
        
        self.config_dir = os.path.join(appdata, "ModernYoutubeDownloader")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.filename = os.path.join(self.config_dir, "settings.json")
        
        self.defaults = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "default_type": "Video", # Video, Audio
            "default_format": "mp4", # mp4, mkv / mp3
            "default_quality": "best",
            "open_folder_after": True,
            "theme_mode": "Dark", # System, Dark, Light
            "accent_color": "crimson_red", 
            "language": "English"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filename):
            data = self.defaults.copy()
        else:
            try:
                with open(self.filename, 'r') as f:
                    data = {**self.defaults, **json.load(f)}
            except:
                data = self.defaults.copy()
        
        # Migrations
        ac = data.get("accent_color", "")
        if ac == "red": data["accent_color"] = "crimson_red"
        elif ac == "orange": data["accent_color"] = "golden_orange"
        
        if data.get("theme_mode") == "System":
            data["theme_mode"] = "Dark"
        
        return data

    def save_settings(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

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


class VideoItem(ctk.CTkFrame):
    # ... (same as before) ...
    def __init__(self, parent, info, settings_manager, remove_callback, tr):
        super().__init__(parent)
        self.info = info
        self.settings = settings_manager
        self.remove_callback = remove_callback
        self.tr = tr

        self.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self.thumb_label = ctk.CTkLabel(self, text="", width=80, height=60)
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=5, pady=5)
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
            if os.path.exists(icon_path):
                 try: image = Image.open(icon_path)
                 except: pass

        if image:
            image.thumbnail((80, 60))
            ctk_image = ctk.CTkImage(image, size=image.size)
            self.thumb_label.configure(image=ctk_image)

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


class App(ctk.CTk):
    def __init__(self):
        # Load settings first to apply theme
        self.settings = SettingsManager()
        
        # Apply Theme
        ctk.set_appearance_mode(self.settings.get("theme_mode"))
        color = self.settings.get("accent_color")
        
        # Load custom theme
        default_themes = ["blue", "green", "dark-blue"]
        if color not in default_themes:
             try:
                 theme_path = os.path.join(application_path, "themes", f"{color}.json")
                 ctk.set_default_color_theme(theme_path)
             except Exception as e:
                 print(f"Failed to load theme {color}: {e}")
                 ctk.set_default_color_theme("blue")
        else:
             try: ctk.set_default_color_theme(color)
             except: ctk.set_default_color_theme("blue")

        super().__init__()
        
        # Load translation
        lang_code = self.settings.get("language")
        self.tr = TRANSLATIONS.get(lang_code, TRANSLATIONS["English"])
        
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            
        self.downloader = YoutubeDownloader()
        self.reload_requested = False
        
        self.title(self.tr["title"])
        self.geometry("500x750")
        self.queue_items = []
        self.is_downloading = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Content Main Frame (so settings can slide over it)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)

        # --- Input ---
        input_frame = ctk.CTkFrame(self.main_content)
        input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.settings_btn = ctk.CTkButton(input_frame, text="⚙", width=40, height=35, command=self.toggle_settings)
        self.settings_btn.pack(side="left", padx=(10, 5), pady=10)

        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text=self.tr["paste_link"])
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        self.add_btn = ctk.CTkButton(input_frame, text="+", width=40, height=35, command=self.fetch_info_thread)
        self.add_btn.pack(side="right", padx=(5, 10), pady=10)

        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self.main_content)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.tab_queue = self.tabview.add(self.tr.get("queue_label", "Queue"))
        self.tab_completed = self.tabview.add(self.tr.get("completed", "Completed"))
        
        # Queue Tab Layout
        self.tab_queue.grid_columnconfigure(0, weight=1)
        self.tab_queue.grid_rowconfigure(0, weight=1)
        self.scroll_queue = ctk.CTkScrollableFrame(self.tab_queue, label_text=None, fg_color="transparent")
        self.scroll_queue.grid(row=0, column=0, sticky="nsew")
        
        # Completed Tab Layout
        self.tab_completed.grid_columnconfigure(0, weight=1)
        self.tab_completed.grid_rowconfigure(0, weight=1)
        self.scroll_completed = ctk.CTkScrollableFrame(self.tab_completed, label_text=None, fg_color="transparent")
        self.scroll_completed.grid(row=0, column=0, sticky="nsew")

        # --- Footer ---
        footer = ctk.CTkFrame(self.main_content, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        self.start_btn = ctk.CTkButton(footer, text=self.tr["start_all"], height=50, font=ctk.CTkFont(size=18, weight="bold"), command=self.start_download_queue)
        self.start_btn.pack(fill="x")
        
        # --- Settings Panel (Init hidden) ---
        self.settings_panel = SettingsPanel(self, self.settings, self.request_reload)
        self.settings_visible = False
        self.settings_panel.place(relx=-0.85, rely=0, relwidth=0.8, relheight=1)

    def toggle_settings(self):
        if self.settings_visible:
            self.animate_settings(-0.85)
            self.settings_visible = False
        else:
            self.settings_panel.lift() # Bring to top
            self.animate_settings(0)
            self.settings_visible = True

    def animate_settings(self, target_RelX):
        # Current POS
        # We assume frame is at some relx. We can't query relx easily from tkinter place_info always returning proper float.
        # So we step towards target.
        # Simple hack: just jump for now OR 
        # Smooth animation:
        start_x = 0 if target_RelX == -0.85 else -0.85
        if target_RelX == 0:
             self.settings_panel.place(relx=0, rely=0, relwidth=0.8, relheight=1)
        else:
             self.settings_panel.place(relx=-0.85, rely=0, relwidth=0.8, relheight=1)

    def open_settings(self):
        self.toggle_settings()

    def request_reload(self):
        self.reload_requested = True
        self.destroy()

    def fetch_info_thread(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.add_btn.configure(state="disabled")
        self.loading_animation_active = True
        self.animate_loading_button()
        threading.Thread(target=self.fetch_info, args=(url,)).start()

    def animate_loading_button(self):
        """Dönen yükleme animasyonu"""
        if not hasattr(self, 'loading_animation_active') or not self.loading_animation_active:
            return
        
        loading_chars = ["◐", "◓", "◑", "◒"]
        if not hasattr(self, 'loading_index'):
            self.loading_index = 0
        
        self.add_btn.configure(text=loading_chars[self.loading_index % len(loading_chars)])
        self.loading_index += 1
        self.after(150, self.animate_loading_button)

    def fetch_info(self, url):
        info = self.downloader.get_info(url)
        self.after(0, self.add_to_queue, info)

    def add_to_queue(self, info):
        # Yükleme animasyonunu durdur
        self.loading_animation_active = False
        self.add_btn.configure(state="normal", text="+")
        self.url_entry.delete(0, "end")
        
        if 'error' in info:
            print(f"Error: {info['error']}")
            return

        item = VideoItem(self.scroll_queue, info, self.settings, self.remove_item, self.tr)
        item.pack(fill="x", padx=5, pady=5)
        self.queue_items.append(item)

    def remove_item(self, item):
        if item in self.queue_items:
            self.queue_items.remove(item)
            item.destroy()

    def start_download_queue(self):
        if self.is_downloading: return
        if not self.queue_items: return

        self.is_downloading = True
        self.start_btn.configure(state="disabled", text=self.tr["downloading"])
        
        threading.Thread(target=self.process_queue).start()

    def process_queue(self):
        for item in self.queue_items:
            if item.status_label.cget("text") == self.tr["completed"]: continue
            
            # Reset UI
            self.after(0, lambda i=item: i.progress.grid())
            self.after(0, lambda i=item: i.progress.set(0))
            self.after(0, lambda i=item: i.status_label.configure(text=self.tr["downloading"], text_color=("blue", "#3B8ED0")))
            
            opts = item.get_options()
            url = item.info.get('webpage_url')
            
            # İndirilen dosyaları takip et
            seen_files = set()
            
            def make_progress_hook(current_item, files_set):
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        try:
                            filename = d.get('filename', '')
                            downloaded = d.get('downloaded_bytes', 0)
                            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                            
                            if total > 0:
                                file_progress = downloaded / total
                                # Kaç dosya indirildi?
                                num_seen = len(files_set)
                                if filename not in files_set:
                                    files_set.add(filename)
                                    num_seen = len(files_set)
                                
                                # Video+Audio = 2 dosya varsayımı
                                base_progress = (num_seen - 1) * 0.5 if num_seen > 0 else 0
                                current_progress = file_progress * 0.5
                                overall = min(base_progress + current_progress, 1.0)
                                
                                self.after(0, lambda p=overall, i=current_item: i.progress.set(p))
                                
                                # Aşama belirteci
                                if num_seen <= 1:
                                    self.after(0, lambda i=current_item: i.status_label.configure(text="📹 Video indiriliyor...", text_color=("blue", "#3B8ED0")))
                                else:
                                    self.after(0, lambda i=current_item: i.status_label.configure(text="🔊 Ses indiriliyor...", text_color=("purple", "#9B59B6")))
                        except:
                            pass
                    elif d['status'] == 'finished':
                        self.after(0, lambda i=current_item: i.progress.set(1.0))
                    
                    # Post-processing durumu
                    if d.get('status') == 'finished' and d.get('postprocessor'):
                        self.after(0, lambda i=current_item: i.status_label.configure(text="⚙️ Birleştiriliyor...", text_color=("orange", "#FFA500")))
                    elif d.get('postprocessor'):
                        self.after(0, lambda i=current_item: i.status_label.configure(text="⚙️ Birleştiriliyor...", text_color=("orange", "#FFA500")))
                
                return progress_hook
            
            hook = make_progress_hook(item, seen_files)
            res = self.downloader.download_video(url, opts, progress_callback=hook)
            
            if res == "Success":
                 self.after(0, lambda i=item: self.move_to_completed(i))
            else:
                 self.after(0, lambda i=item: i.status_label.configure(text=self.tr["failed"], text_color=("red", "#E04F5F")))

        self.is_downloading = False
        self.after(0, lambda: self.start_btn.configure(state="normal", text=self.tr["start_all"]))
        
        # Check if open folder enabled (opens default path)
        if self.settings.get("open_folder_after"):
             path = self.settings.get("download_path")
             self.after(0, lambda: self.open_download_folder(path))

    def move_to_completed(self, item):
        item.status_label.configure(text=self.tr["completed"], text_color=("green", "#2CC985"))
        item.progress.grid_remove() 
        
        if item in self.queue_items:
            self.queue_items.remove(item)
            
        item.pack_forget()
        item.destroy()
        
        # Create new item in completed tab
        # We need to ensure we pass correct args. 
        # Using a slightly modified VideoItem or just configuring it?
        # Simpler to create new instance.
        new_item = VideoItem(self.scroll_completed, item.info, self.settings, lambda i: i.destroy(), self.tr)
        new_item.pack(fill="x", padx=5, pady=5)
        new_item.status_label.configure(text=self.tr["completed"], text_color=("green", "#2CC985"))
        new_item.progress.grid_remove()
        
        # Modify UI
        new_item.type_menu.grid_remove()
        new_item.quality_menu.grid_remove()
        new_item.remove_btn.configure(text="X", width=30, fg_color="red", hover_color="darkred", command=lambda: new_item.destroy())
        
        # Open Folder Button
        path = item.get_options()['output_path']
        open_btn = ctk.CTkButton(new_item, text="📂", width=40, height=20, fg_color="gray", command=lambda: self.open_download_folder(path))
        open_btn.grid(row=1, column=1, padx=5, pady=2, sticky="w")

    def open_download_folder(self, path=None):
        if not path: path = self.settings.get("download_path")
        if hasattr(os, 'startfile'):
            try: os.startfile(path)
            except: pass
        elif sys.platform == 'darwin':
            try: subprocess.call(['open', path])
            except: pass
        else:
            try: subprocess.call(['xdg-open', path])
            except: pass


if __name__ == "__main__":
    while True:
        app = App()
        app.mainloop()
        if not app.reload_requested:
            break
