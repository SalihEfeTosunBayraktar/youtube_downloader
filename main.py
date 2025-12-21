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

# Determine paths
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(application_path, "app_icon.ico")

# Localization Dictionary
TRANSLATIONS = {
    "English": {
        "title": "Modern YouTube Downloader",
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
        "audio": "Audio"
    },
    "Turkish": {
        "title": "Modern YouTube İndirici",
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
        "audio": "Ses"
    }
}

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.defaults = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "default_type": "Video", # Video, Audio
            "default_format": "mp4", # mp4, mkv / mp3
            "default_quality": "best",
            "open_folder_after": True,
            "theme_mode": "Dark", # System, Dark, Light
            "accent_color": "crimson_red", # default to crimson red (close to user request)
            "language": "English"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filename):
            return self.defaults.copy()
        try:
            with open(self.filename, 'r') as f:
                return {**self.defaults, **json.load(f)}
        except:
            return self.defaults.copy()

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

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, manager, reload_callback):
        super().__init__(parent)
        self.manager = manager
        self.reload_callback = reload_callback
        
        # Load localized strings
        self.lang_code = self.manager.get("language")
        self.tr = TRANSLATIONS.get(self.lang_code, TRANSLATIONS["English"])
        
        self.title(self.tr["settings_title"])
        self.geometry("400x750")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        if os.path.exists(icon_path):
            self.after(200, lambda: self.iconbitmap(icon_path))

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=self.tr["settings_title"], font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Language
        lang_frame = ctk.CTkFrame(self)
        lang_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(lang_frame, text=self.tr["language"]).pack(anchor="w", padx=10, pady=5)
        
        self.lang_var = ctk.StringVar(value=self.lang_code)
        ctk.CTkOptionMenu(lang_frame, values=["English", "Turkish"], variable=self.lang_var).pack(fill="x", padx=10, pady=5)


        # Download Path
        path_frame = ctk.CTkFrame(self)
        path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(path_frame, text=self.tr["download_loc"]).pack(anchor="w", padx=10, pady=5)
        
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text=self.manager.get("download_path"))
        self.path_entry.insert(0, self.manager.get("download_path"))
        self.path_entry.configure(state="disabled")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        ctk.CTkButton(path_frame, text=self.tr["browse"], width=60, command=self.browse_path).pack(side="right", padx=(5, 10), pady=10)

        # Appearance
        app_frame = ctk.CTkFrame(self)
        app_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(app_frame, text=self.tr["appearance"]).pack(anchor="w", padx=10, pady=5)

        self.theme_var = ctk.StringVar(value=self.manager.get("theme_mode"))
        self.theme_menu = ctk.CTkOptionMenu(app_frame, values=["System", "Dark", "Light"], variable=self.theme_var, command=self.on_theme_change)
        self.theme_menu.pack(fill="x", padx=10, pady=5)
        
        # Load color list from generated files or static list
        self.color_names = [
            "Electric Blue", "Neon Cyan", "Emerald Green", "Mint Green", "Lime Green", "Amber Yellow",
            "Golden Orange", "Deep Orange", "Coral Red", "Crimson Red", "Hot Pink", "Rose Pink",
            "Magenta", "Royal Purple", "Indigo Blue", "Midnight Blue", "Teal", "Ocean Blue", "Steel Blue",
            "Slate Gray", "Cyber Yellow", "Neon Green", "Violet Glow", "Turquoise Glow"
        ]
        
        current_accent = self.manager.get("accent_color").replace("_", " ").title()
        # map back to display name if simple name
        fixed_display_name = next((name for name in self.color_names if name.lower().replace(" ", "_") == self.manager.get("accent_color")), current_accent)
        
        self.color_var = ctk.StringVar(value=fixed_display_name)
        self.color_menu = ctk.CTkOptionMenu(app_frame, values=self.color_names, variable=self.color_var)
        self.color_menu.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(app_frame, text=self.tr["restart_hint"], font=("Arial", 10), text_color="gray").pack(anchor="w", padx=10, pady=(0,5))


        # Defaults
        defaults_frame = ctk.CTkFrame(self)
        defaults_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(defaults_frame, text=self.tr["def_options"]).pack(anchor="w", padx=10, pady=5)

        self.type_var = ctk.StringVar(value=self.manager.get("default_type"))
        ctk.CTkOptionMenu(defaults_frame, values=[self.tr["video"], self.tr["audio"]], variable=self.type_var, command=self.update_formats).pack(fill="x", padx=10, pady=5)

        self.format_var = ctk.StringVar(value=self.manager.get("default_format"))
        self.format_menu = ctk.CTkOptionMenu(defaults_frame, values=["mp4", "mkv"], variable=self.format_var)
        self.format_menu.pack(fill="x", padx=10, pady=5)

        self.quality_var = ctk.StringVar(value=self.manager.get("default_quality"))
        self.quality_menu = ctk.CTkOptionMenu(defaults_frame, values=["best", "1080p", "720p", "480p"], variable=self.quality_var)
        self.quality_menu.pack(fill="x", padx=10, pady=5)

        # Open Folder Checkbox
        self.open_folder_var = ctk.BooleanVar(value=self.manager.get("open_folder_after"))
        ctk.CTkCheckBox(self, text=self.tr["open_folder"], variable=self.open_folder_var).grid(row=5, column=0, padx=20, pady=20, sticky="w")

        # Save Button
        ctk.CTkButton(self, text=self.tr["save"], command=self.save_and_close).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

        # Footer
        ctk.CTkLabel(self, text=self.tr["created_by"], text_color="gray", font=("Arial", 10)).grid(row=7, column=0, pady=10)

        self.update_formats(self.type_var.get())

    def on_theme_change(self, mode):
        if mode == "System":
            self.color_menu.configure(state="disabled")
        else:
            self.color_menu.configure(state="normal")

    def update_formats(self, choice):
        if choice == self.tr["audio"] or choice == "Audio":
            self.format_menu.configure(values=["mp3", "m4a", "wav"])
            self.quality_menu.configure(values=["320", "256", "192", "128"])
        else:
            self.format_menu.configure(values=["mp4", "mkv", "webm"])
            self.quality_menu.configure(values=["best", "1080p", "720p", "480p"])

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            self.path_entry.configure(state="disabled")

    def save_and_close(self):
        old_theme = self.manager.get("theme_mode")
        old_color = self.manager.get("accent_color")
        old_lang = self.manager.get("language")
        
        new_theme = self.theme_var.get()
        # Convert display name back to safe name
        new_color = self.color_var.get().lower().replace(" ", "_")
        new_lang = self.lang_var.get()
        
        # Map localized types back to Eng
        default_type = "Video"
        if self.type_var.get() == self.tr.get("audio"): default_type = "Audio"

        self.manager.set("download_path", self.path_entry.get())
        self.manager.set("default_type", default_type)
        self.manager.set("default_format", self.format_var.get())
        self.manager.set("default_quality", self.quality_var.get())
        self.manager.set("open_folder_after", self.open_folder_var.get())
        self.manager.set("theme_mode", new_theme)
        self.manager.set("accent_color", new_color)
        self.manager.set("language", new_lang)
        
        self.destroy()

        if old_theme != new_theme or old_color != new_color or old_lang != new_lang:
            self.reload_callback()


class VideoItem(ctk.CTkFrame):
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
        self.quality_menu = ctk.CTkOptionMenu(self, values=["best", "1080p", "720p", "480p"], variable=self.quality_var, width=80, height=20, font=("Arial", 10))
        self.quality_menu.grid(row=1, column=2, padx=5, pady=2, sticky="w")

        # Status / Remove
        self.status_label = ctk.CTkLabel(self, text=self.tr["queued"], text_color="gray", font=("Arial", 10))
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
            self.quality_menu.configure(values=["320", "192", "128"])
            self.quality_var.set("192")
        else:
            self.quality_menu.configure(values=["best", "1080p", "720p"])
            self.quality_var.set("best")

    def load_thumbnail(self, url):
        if not url: return
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            image = Image.open(io.BytesIO(raw_data))
            image.thumbnail((80, 60))
            ctk_image = ctk.CTkImage(image, size=image.size)
            self.thumb_label.configure(image=ctk_image)
        except: pass

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
        
        # Load custom theme if needed
        # We assume all non-default colors have generated themes
        default_themes = ["blue", "green", "dark-blue"]
        if color not in default_themes:
             try:
                 theme_path = os.path.join(application_path, "themes", f"{color}.json")
                 ctk.set_default_color_theme(theme_path)
             except Exception as e:
                 print(f"Failed to load theme {color}: {e}")
                 ctk.set_default_color_theme("blue")
        else:
             try:
                 ctk.set_default_color_theme(color)
             except:
                 ctk.set_default_color_theme("blue")

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
        self.grid_rowconfigure(2, weight=1)

        # --- Header ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(header, text=self.tr["title"], font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        
        self.settings_btn = ctk.CTkButton(header, text="⚙", width=40, height=40, command=self.open_settings)
        self.settings_btn.pack(side="right") 

        # --- Input ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text=self.tr["paste_link"])
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        self.add_btn = ctk.CTkButton(input_frame, text="+", width=40, command=self.fetch_info_thread)
        self.add_btn.pack(side="right", padx=10, pady=10)

        # --- Queue ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text=self.tr["queue_label"])
        self.scroll_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # --- Footer ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.start_btn = ctk.CTkButton(footer, text=self.tr["start_all"], height=50, font=ctk.CTkFont(size=18, weight="bold"), command=self.start_download_queue)
        self.start_btn.pack(fill="x")

    def open_settings(self):
        SettingsDialog(self, self.settings, self.request_reload)

    def request_reload(self):
        self.reload_requested = True
        self.destroy()

    def fetch_info_thread(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.add_btn.configure(state="disabled")
        threading.Thread(target=self.fetch_info, args=(url,)).start()

    def fetch_info(self, url):
        info = self.downloader.get_info(url)
        self.after(0, self.add_to_queue, info)

    def add_to_queue(self, info):
        self.add_btn.configure(state="normal")
        self.url_entry.delete(0, "end")
        
        if 'error' in info:
            print(f"Error: {info['error']}")
            return

        item = VideoItem(self.scroll_frame, info, self.settings, self.remove_item, self.tr)
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
            self.after(0, lambda i=item: i.status_label.configure(text=self.tr["downloading"], text_color="blue"))
            
            opts = item.get_options()
            url = item.info.get('webpage_url')
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        self.after(0, lambda: item.progress.set(float(p)/100))
                    except: pass
                elif d['status'] == 'finished':
                     self.after(0, lambda: item.progress.set(1.0))

            res = self.downloader.download_video(url, opts, progress_callback=progress_hook)
            
            if res == "Success":
                 self.after(0, lambda i=item: i.status_label.configure(text=self.tr["completed"], text_color="green"))
            else:
                 self.after(0, lambda i=item: i.status_label.configure(text=self.tr["failed"], text_color="red"))

        self.is_downloading = False
        self.after(0, lambda: self.start_btn.configure(state="normal", text=self.tr["start_all"]))
        
        # Check if open folder enabled
        if self.settings.get("open_folder_after"):
             self.after(0, self.open_download_folder)

    def open_download_folder(self):
        path = self.settings.get("download_path")
        if os.path.exists(path):
            os.startfile(path)

if __name__ == "__main__":
    while True:
        app = App()
        app.mainloop()
        if not app.reload_requested:
            break
