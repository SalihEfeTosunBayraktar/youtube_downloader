import customtkinter as ctk
import threading
from PIL import Image
import urllib.request
import io
import os
import json
import subprocess
from tkinter import filedialog
from downloader import YoutubeDownloader

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.defaults = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "default_type": "Video", # Video, Audio
            "default_format": "mp4", # mp4, mkv / mp3
            "default_quality": "best",
            "open_folder_after": True,
            "theme_mode": "System", # System, Dark, Light
            "accent_color": "blue" # blue, green, dark-blue
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
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.manager = manager
        self.title("Settings")
        self.geometry("400x650") # Taller for more options
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self, text="Application Settings", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Download Path
        path_frame = ctk.CTkFrame(self)
        path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(path_frame, text="Download Location").pack(anchor="w", padx=10, pady=5)
        
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text=self.manager.get("download_path"))
        self.path_entry.insert(0, self.manager.get("download_path"))
        self.path_entry.configure(state="disabled")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        ctk.CTkButton(path_frame, text="Browse", width=60, command=self.browse_path).pack(side="right", padx=(5, 10), pady=10)

        # Appearance
        app_frame = ctk.CTkFrame(self)
        app_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(app_frame, text="Appearance").pack(anchor="w", padx=10, pady=5)

        self.theme_var = ctk.StringVar(value=self.manager.get("theme_mode"))
        ctk.CTkOptionMenu(app_frame, values=["System", "Dark", "Light"], variable=self.theme_var, command=self.change_theme_mode).pack(fill="x", padx=10, pady=5)
        
        self.color_var = ctk.StringVar(value=self.manager.get("accent_color"))
        ctk.CTkOptionMenu(app_frame, values=["blue", "green", "dark-blue"], variable=self.color_var, command=self.change_accent_color).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(app_frame, text="* Restart required for accent color", font=("Arial", 10), text_color="gray").pack(anchor="w", padx=10, pady=(0,5))


        # Defaults
        defaults_frame = ctk.CTkFrame(self)
        defaults_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(defaults_frame, text="Default Download Options").pack(anchor="w", padx=10, pady=5)

        self.type_var = ctk.StringVar(value=self.manager.get("default_type"))
        ctk.CTkOptionMenu(defaults_frame, values=["Video", "Audio"], variable=self.type_var, command=self.update_formats).pack(fill="x", padx=10, pady=5)

        self.format_var = ctk.StringVar(value=self.manager.get("default_format"))
        self.format_menu = ctk.CTkOptionMenu(defaults_frame, values=["mp4", "mkv"], variable=self.format_var)
        self.format_menu.pack(fill="x", padx=10, pady=5)

        self.quality_var = ctk.StringVar(value=self.manager.get("default_quality"))
        self.quality_menu = ctk.CTkOptionMenu(defaults_frame, values=["best", "1080p", "720p", "480p"], variable=self.quality_var)
        self.quality_menu.pack(fill="x", padx=10, pady=5)

        # Open Folder Checkbox
        self.open_folder_var = ctk.BooleanVar(value=self.manager.get("open_folder_after"))
        ctk.CTkCheckBox(self, text="Open folder after download", variable=self.open_folder_var).grid(row=4, column=0, padx=20, pady=20, sticky="w")

        # Save Button
        ctk.CTkButton(self, text="Save Settings", command=self.save_and_close).grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        self.update_formats(self.type_var.get())

    def change_theme_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def change_accent_color(self, color):
        # Applies to new widgets only unless restarted, but we can try
        # ctk.set_default_color_theme(color) 
        pass 

    def update_formats(self, choice):
        if choice == "Audio":
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
        self.manager.set("download_path", self.path_entry.get())
        self.manager.set("default_type", self.type_var.get())
        self.manager.set("default_format", self.format_var.get())
        self.manager.set("default_quality", self.quality_var.get())
        self.manager.set("open_folder_after", self.open_folder_var.get())
        self.manager.set("theme_mode", self.theme_var.get())
        self.manager.set("accent_color", self.color_var.get())
        self.destroy()


class VideoItem(ctk.CTkFrame):
    def __init__(self, parent, info, settings_manager, remove_callback):
        super().__init__(parent)
        self.info = info
        self.settings = settings_manager
        self.remove_callback = remove_callback

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
        self.type_menu = ctk.CTkOptionMenu(self, values=["Video", "Audio"], variable=self.type_var, width=80, height=20, font=("Arial", 10), command=self.update_options)
        self.type_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        self.quality_var = ctk.StringVar(value=self.settings.get("default_quality"))
        self.quality_menu = ctk.CTkOptionMenu(self, values=["best", "1080p", "720p", "480p"], variable=self.quality_var, width=80, height=20, font=("Arial", 10))
        self.quality_menu.grid(row=1, column=2, padx=5, pady=2, sticky="w")

        # Status / Remove
        self.status_label = ctk.CTkLabel(self, text="Queued", text_color="gray", font=("Arial", 10))
        self.status_label.grid(row=2, column=1, padx=5, pady=(0,5), sticky="w")

        self.remove_btn = ctk.CTkButton(self, text="X", width=30, height=20, fg_color="red", hover_color="darkred", command=lambda: self.remove_callback(self))
        self.remove_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ne")

        # Progress
        self.progress = ctk.CTkProgressBar(self, height=5)
        self.progress.set(0)
        self.progress.grid(row=3, column=0, columnspan=4, padx=5, pady=(0,5), sticky="ew")
        self.progress.grid_remove()

        self.update_options(self.type_var.get())

        # Restore default if needed because update_options resets
        self.quality_var.set(self.settings.get("default_quality"))


    def update_options(self, choice):
        if choice == "Audio":
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
        ext_map = {"Video": "mp4", "Audio": "mp3"} # Simple mapping
        return {
            "format_type": self.type_var.get().lower(),
            "quality": self.quality_var.get(),
            "ext": ext_map.get(self.type_var.get(), "mp4"),
            "is_playlist": self.info.get('is_playlist', False),
            "output_path": self.settings.get("download_path")
        }

class App(ctk.CTk):
    def __init__(self):
        # Load settings first to apply theme
        self.settings = SettingsManager()
        
        # Apply Theme
        ctk.set_appearance_mode(self.settings.get("theme_mode"))
        try:
            ctk.set_default_color_theme(self.settings.get("accent_color"))
        except:
             ctk.set_default_color_theme("blue")

        super().__init__()
        
        self.downloader = YoutubeDownloader()
        
        self.title("YT Downloader")
        self.geometry("500x750")
        self.queue_items = []
        self.is_downloading = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Header ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(header, text="YouTube Downloader", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        
        self.settings_btn = ctk.CTkButton(header, text="⚙", width=40, height=40, command=self.open_settings)
        self.settings_btn.pack(side="right")

        # --- Input ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="Paste Link...")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        self.add_btn = ctk.CTkButton(input_frame, text="+", width=40, command=self.fetch_info_thread)
        self.add_btn.pack(side="right", padx=10, pady=10)

        # --- Queue ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Download Queue")
        self.scroll_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # --- Footer ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.start_btn = ctk.CTkButton(footer, text="Start Download All", height=50, font=ctk.CTkFont(size=18, weight="bold"), command=self.start_download_queue)
        self.start_btn.pack(fill="x")

    def open_settings(self):
        SettingsDialog(self, self.settings)

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
            # Simple error dialog or toast could go here
            print(f"Error: {info['error']}")
            return

        item = VideoItem(self.scroll_frame, info, self.settings, self.remove_item)
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
        self.start_btn.configure(state="disabled", text="Downloading...")
        
        threading.Thread(target=self.process_queue).start()

    def process_queue(self):
        for item in self.queue_items:
            if item.status_label.cget("text") == "Completed": continue
            
            # Reset UI
            self.after(0, lambda i=item: i.progress.grid())
            self.after(0, lambda i=item: i.status_label.configure(text="Downloading...", text_color="blue"))
            
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
                 self.after(0, lambda i=item: i.status_label.configure(text="Completed", text_color="green"))
            else:
                 self.after(0, lambda i=item: i.status_label.configure(text="Failed", text_color="red"))

        self.is_downloading = False
        self.after(0, lambda: self.start_btn.configure(state="normal", text="Start Download All"))
        
        # Check if open folder enabled
        if self.settings.get("open_folder_after"):
             self.after(0, self.open_download_folder)

    def open_download_folder(self):
        path = self.settings.get("download_path")
        if os.path.exists(path):
            os.startfile(path)

if __name__ == "__main__":
    app = App()
    app.mainloop()
