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
