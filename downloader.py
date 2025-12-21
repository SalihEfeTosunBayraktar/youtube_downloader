import yt_dlp
import os
import sys
import shutil
import threading

def get_ffmpeg_path():
    """Returns the path to the bundled ffmpeg executable."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller temp folder
        ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
    
    # Check local directory
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # Check PATH
    return shutil.which('ffmpeg')

def make_unique(path):
    """
    Ensures the path does not exist by appending (1), (2), etc.
    """
    if not os.path.exists(path):
        return path
    
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = f"{base} ({counter}){ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base} ({counter}){ext}"
    
    return new_path

class UniqueYoutubeDL(yt_dlp.YoutubeDL):
    def prepare_filename(self, info_dict, *args, **kwargs):
        # robustly call super
        try:
            path = super().prepare_filename(info_dict, *args, **kwargs)
            return make_unique(path)
        except Exception:
            # Fallback if signature mismatch or other error
            try:
                # Try simple call
                path = super().prepare_filename(info_dict)
                return make_unique(path)
            except:
                # Ultimate fallback
                filename = info_dict.get('_filename')
                if not filename:
                    title = info_dict.get('title', 'video')
                    ext = info_dict.get('ext', 'mp4')
                    filename = f"{title}.{ext}"
                return make_unique(filename)

class YoutubeDownloader:
    def __init__(self):
        ffmpeg_exe = get_ffmpeg_path()
        self.ffmpeg_location = os.path.dirname(ffmpeg_exe) if ffmpeg_exe else None
        
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_location
        }

    def get_info(self, url):
        """Fetches metadata for the given URL."""
        try:
            # Hızlı bilgi alma için optimize edilmiş seçenekler
            fast_opts = {
                **self.ydl_opts,
                'extract_flat': 'in_playlist',  # Playlist'te sadece temel bilgileri al
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(fast_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'is_playlist': 'entries' in info,
                    'webpage_url': info.get('webpage_url') or url,
                }
        except Exception as e:
            return {'error': str(e)}

    def download_video(self, url, options, progress_callback=None):
        """
        Downloads the video with specified options.
        """
        output_path = options.get('output_path', os.getcwd())
        
        # Base options
        # NOTE: We use UniqueYoutubeDL so we don't need manual duplicate checks here.
        
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else [],
            'noplaylist': True, 
            'ffmpeg_location': self.ffmpeg_location,
            'ignoreerrors': True,
            'overwrites': True, # We handle uniqueness via filename change
        }

        if options.get('is_playlist'):
            ydl_opts['noplaylist'] = False
            # Playlist subfolder structure: output_path/PlaylistName/
            ydl_opts['outtmpl'] = os.path.join(output_path, '%(playlist_title)s', '%(title)s.%(ext)s')

        # Format selection
        if options.get('format_type') == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('ext', 'mp3'),
                'preferredquality': options.get('quality', '192'),
            }]
        else:
            # Video
            quality = options.get('quality', 'best')
            ext = options.get('ext', 'mp4')
            
            if quality == 'best':
                 ydl_opts['format'] = f"bestvideo+bestaudio/best"
            else:
                 height = quality.split('p')[0]
                 if height.isdigit():
                     ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
                 else:
                     ydl_opts['format'] = f"bestvideo+bestaudio/best"

            ydl_opts['merge_output_format'] = ext
            
            # Opus codec'ini AAC'ye dönüştür (basit oynatıcılarda uyumluluk için)
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': ext,
            }]
            ydl_opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']

        try:
            # Use UniqueYoutubeDL to enforce unique filenames
            with UniqueYoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return "Success"
        except Exception as e:
            return str(e)

# Example usage for testing
if __name__ == "__main__":
    dl = YoutubeDownloader()
    # print(dl.get_info("..."))
