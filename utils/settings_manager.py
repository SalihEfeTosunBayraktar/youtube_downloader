import os
import json

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
            "open_folder_after": True,
            "theme_mode": "Dark", 
            "accent_color": "crimson_red", 
            "language": "English",
            
            # Separated Defaults
            "default_add_type": "Video", # Video, Audio, Thumbnail
            
            "video_format": "mp4",
            "video_quality": "best",
            
            "audio_format": "mp3",
            "audio_quality": "192",
            
            "thumb_format": "jpg",
            "thumb_quality": "Original"
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
            
        # Migrate old format keys to new separated keys if separate ones are missing
        if "default_type" in data and "default_add_type" not in data:
            data["default_add_type"] = data["default_type"]
            
        # We can't easily map old single format/quality to 3 separate ones perfectly, 
        # but we can try to preserve user intent if they had a weird default.
        # Actually it's safer to ensure the new keys exist with defaults if they don't.
        for k, v in self.defaults.items():
            if k not in data:
                data[k] = v
        
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
