import customtkinter as ctk
import threading
from PIL import Image
import urllib.request
import io
from downloader import YoutubeDownloader

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern YouTube Downloader")
        self.geometry("900x600")
        self.min_size(500, 600)

        # Helper
        self.downloader = YoutubeDownloader()
        self.current_video_info = None

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Main content area expands

        # --- Top Bar (URL Input) ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Paste YouTube Link Here...")
        self.url_entry.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")
        
        self.fetch_btn = ctk.CTkButton(self.top_frame, text="Fetch", width=100, command=self.fetch_info_thread)
        self.fetch_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # --- Content Area ---
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        # We will dynamically pack/grid things here based on fetched info

        # Placeholder message
        self.status_label = ctk.CTkLabel(self.content_frame, text="Ready to download", font=ctk.CTkFont(size=16))
        self.status_label.pack(expand=True)

        # Preview Widgets (Hidden initially)
        self.preview_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        self.thumb_label = ctk.CTkLabel(self.preview_frame, text="")
        self.thumb_label.pack(pady=10)
        
        self.title_label = ctk.CTkLabel(self.preview_frame, text="", font=ctk.CTkFont(size=18, weight="bold"), wraplength=400)
        self.title_label.pack(pady=5)
        
        self.meta_label = ctk.CTkLabel(self.preview_frame, text="", text_color="gray")
        self.meta_label.pack(pady=5)

        # --- Settings / Action Area ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.settings_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Type Selection
        self.type_var = ctk.StringVar(value="Video")
        self.type_menu = ctk.CTkOptionMenu(self.settings_frame, values=["Video", "Audio"], variable=self.type_var, command=self.update_options)
        self.type_menu.grid(row=0, column=0, padx=10, pady=20)

        # Format Selection
        self.format_var = ctk.StringVar(value="mp4")
        self.format_menu = ctk.CTkOptionMenu(self.settings_frame, values=["mp4", "mkv"], variable=self.format_var)
        self.format_menu.grid(row=0, column=1, padx=10, pady=20)

        # Quality Selection
        self.quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkOptionMenu(self.settings_frame, values=["best", "1080p", "720p", "480p"], variable=self.quality_var)
        self.quality_menu.grid(row=0, column=2, padx=10, pady=20)

        # Download Button
        self.download_btn = ctk.CTkButton(self.settings_frame, text="Download Now", font=ctk.CTkFont(size=16, weight="bold"), height=40, fg_color="#E50914", hover_color="#B20710", command=self.start_download_thread)
        self.download_btn.grid(row=0, column=3, padx=20, pady=20, sticky="ew")

        # Progress Bar overlay (bottom of settings or content)
        self.progress_bar = ctk.CTkProgressBar(self.settings_frame, orientation="horizontal")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.grid_remove() # Hide initially

    def update_options(self, choice):
        if choice == "Audio":
            self.format_menu.configure(values=["mp3", "m4a", "wav"])
            self.format_var.set("mp3")
            self.quality_menu.configure(values=["320", "256", "192", "128"])
            self.quality_var.set("192")
        else:
            self.format_menu.configure(values=["mp4", "mkv", "webm"])
            self.format_var.set("mp4")
            self.quality_menu.configure(values=["best", "1080p", "720p", "480p"])
            self.quality_var.set("best")

    def fetch_info_thread(self):
        url = self.url_entry.get()
        if not url:
            return
        self.fetch_btn.configure(state="disabled")
        self.status_label.configure(text="Fetching metadata...")
        self.status_label.pack(expand=True)
        self.preview_frame.pack_forget()
        
        threading.Thread(target=self.fetch_info, args=(url,)).start()

    def fetch_info(self, url):
        info = self.downloader.get_info(url)
        self.after(0, self.update_ui_with_info, info)

    def update_ui_with_info(self, info):
        self.fetch_btn.configure(state="normal")
        if 'error' in info:
            self.status_label.configure(text=f"Error: {info['error']}")
            return

        self.current_video_info = info
        self.status_label.pack_forget()
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Update Text
        self.title_label.configure(text=info.get('title', 'Unknown Title'))
        self.meta_label.configure(text=f"{info.get('uploader', 'Unknown')} • {self.format_seconds(info.get('duration', 0))}")

        # Update Thumbnail
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            self.load_thumbnail(thumbnail_url)

    def load_thumbnail(self, url):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            image = Image.open(io.BytesIO(raw_data))
            # Resize keeping aspect ratio roughly
            image.thumbnail((400, 300))
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.thumb_label.configure(image=ctk_image, text="")
        except Exception as e:
            print(f"Thumb error: {e}")
            self.thumb_label.configure(text="[No Image]", image=None)

    def format_seconds(self, seconds):
        if not seconds: return "0:00"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def start_download_thread(self):
        if not self.current_video_info:
            return
        
        self.download_btn.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.set(0)
        
        options = {
            'format_type': self.type_var.get().lower(),
            'ext': self.format_var.get(),
            'quality': self.quality_var.get(),
            'is_playlist': self.current_video_info.get('is_playlist', False)
        }
        url = self.current_video_info.get('webpage_url')

        threading.Thread(target=self.run_download, args=(url, options)).start()

    def run_download(self, url, options):
        # Callback for progress
        def progress_hook(d):
            if d['status'] == 'downloading':
                # Calculate percentage
                try:
                    p = d.get('_percent_str', '0%').replace('%','')
                    self.after(0, self.progress_bar.set, float(p)/100)
                except: 
                    pass
            elif d['status'] == 'finished':
                self.after(0, self.progress_bar.set, 1.0)

        success = self.downloader.download_video(url, options, progress_callback=progress_hook)
        self.after(0, self.download_finished, success)

    def download_finished(self, success):
        self.download_btn.configure(state="normal")
        self.progress_bar.grid_remove()
        if success:
            self.status_label.configure(text="Download Complete!")
            self.status_label.pack(side="bottom", pady=5)
            self.after(3000, self.status_label.pack_forget)
        else:
            self.status_label.configure(text="Download Failed.")
            self.status_label.pack(side="bottom", pady=5)

if __name__ == "__main__":
    app = App()
    app.mainloop()
