import customtkinter as ctk
import threading
import os
import sys
import subprocess
from downloader import YoutubeDownloader
from utils.settings_manager import SettingsManager
from utils.locales import TRANSLATIONS
from .settings_panel import SettingsPanel
from .components import VideoItem

class App(ctk.CTk):
    def __init__(self):
        # Determine paths
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            # If running from gui/app.py context, we need to go up one level
            # But normally we rely on __file__ being relative to root or similar
            # Let's assume standard structure:
            application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if 'gui' not in application_path and 'utils' not in application_path:
                 pass # Might be running directly? Unlikely.
        
        self.icon_path = os.path.join(application_path, "app_icon.ico")

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
        
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
            
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

        item = VideoItem(self.scroll_queue, info, self.settings, self.remove_item, self.tr, self.icon_path)
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
        # Iterate over a copy of the list to allow safe removal modification during iteration
        items_to_process = list(self.queue_items)
        for item in items_to_process:
            # Check if item is valid/not destroyed before starting
            try:
                if not item.winfo_exists(): continue
                # Re-check if it's still in the main list (might have been removed individually)
                if item not in self.queue_items: continue
                if item.status_label.cget("text") == self.tr["completed"]: continue
            except: continue
            
            # Reset UI
            self.after(0, lambda i=item: self._safe_ui_update(i, "progress_grid"))
            self.after(0, lambda i=item: self._safe_ui_update(i, "progress_set", 0))
            self.after(0, lambda i=item: self._safe_ui_update(i, "status", self.tr["downloading"], ("blue", "#3B8ED0")))
            
            opts = item.get_options()
            url = item.info.get('original_url') or item.info.get('webpage_url')
            is_playlist = item.info.get('is_playlist', False)
            playlist_count = item.info.get('playlist_count', 0)
            
            # İndirilen dosyaları takip et
            seen_files = set()
            
            def make_progress_hook(current_item, files_set, p_count):
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
                                
                                # Progress Calculation
                                if p_count and p_count > 1:
                                    # Playlist Mode: (Completed Videos + Current Video Progress) / Total Videos
                                    # num_seen works as "currently processing Nth file"
                                    # BUT video + audio are separate files usually.
                                    # Approximation: divide seen by 2 or rely on filename change?
                                    # Simple approach: Each video is 1 unit.
                                    # If we assume 1 file per video (merged) or we ignore duplicates:
                                    overall = (num_seen - 1 + file_progress) / p_count
                                else:
                                    # Single Video Mode (Video + Audio = 2 files assumption)
                                    base_progress = (num_seen - 1) * 0.5 if num_seen > 0 else 0
                                    current_progress = file_progress * 0.5
                                    overall = min(base_progress + current_progress, 1.0)
                                
                                self.after(0, lambda p=overall, i=current_item: self._safe_ui_update(i, "progress_set", p))
                                
                                # Aşama belirteci
                                text_key = "status_video_downloading"
                                if num_seen > 1 and not p_count: text_key = "status_audio_downloading"
                                
                                color = ("blue", "#3B8ED0") if text_key == "status_video_downloading" else ("purple", "#9B59B6")
                                
                                self.after(0, lambda i=current_item: self._safe_ui_update(i, "status", self.tr.get(text_key, "..."), color))
                        except Exception as e:
                            # print(f"Progress error: {e}") 
                            pass
                    elif d['status'] == 'finished':
                         if not p_count: # Single video finished
                             self.after(0, lambda i=current_item: self._safe_ui_update(i, "progress_set", 1.0))
                    
                    # Post-processing durumu
                    if d.get('postprocessor'):
                        self.after(0, lambda i=current_item: self._safe_ui_update(i, "status", self.tr.get("status_merging", "Merging..."), ("orange", "#FFA500")))

                return progress_hook
            
            hook = make_progress_hook(item, seen_files, playlist_count)
            res = self.downloader.download_video(url, opts, progress_callback=hook)
            
            if res == "Success":
                 self.after(0, lambda i=item: self.move_to_completed(i))
            else:
                 self.after(0, lambda i=item: self._safe_ui_update(i, "status", self.tr["failed"], ("red", "#E04F5F")))

        self.is_downloading = False
        self.after(0, lambda: self.start_btn.configure(state="normal", text=self.tr["start_all"]))
        
        # Check if open folder enabled (opens default path)
        if self.settings.get("open_folder_after"):
             path = self.settings.get("download_path")
             self.after(0, lambda: self.open_download_folder(path))

    def _safe_ui_update(self, item, action, *args):
        try:
            if not item.winfo_exists(): return
            
            if action == "progress_grid":
                item.progress.grid()
            elif action == "progress_set":
                item.progress.set(args[0])
            elif action == "status":
                item.status_label.configure(text=args[0], text_color=args[1])
        except:
            pass

    def move_to_completed(self, item):
        item.status_label.configure(text=self.tr["completed"], text_color=("green", "#2CC985"))
        item.progress.grid_remove() 
        
        if item in self.queue_items:
            self.queue_items.remove(item)
            
        item.pack_forget()
        item.destroy()
        
        # Create new item in completed tab
        new_item = VideoItem(self.scroll_completed, item.info, self.settings, lambda i: i.destroy(), self.tr, self.icon_path)
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
