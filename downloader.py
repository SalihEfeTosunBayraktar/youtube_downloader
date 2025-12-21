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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filename_cache = {} # {original_base_path: unique_base_path}

    def prepare_filename(self, info_dict, *args, **kwargs):
        try:
            path = super().prepare_filename(info_dict, *args, **kwargs)
            
            # Split to get base
            base, ext = os.path.splitext(path)
            
            # Check cache first to ensure consistency between video/audio parts
            if base in self._filename_cache:
                return f"{self._filename_cache[base]}{ext}"
            
            # Determine unique name
            unique_path = make_unique(path)
            unique_base, _ = os.path.splitext(unique_path)
            
            # Cache the decision
            self._filename_cache[base] = unique_base
            
            return unique_path
        except Exception:
            # Fallback
            try:
                path = super().prepare_filename(info_dict)
                return make_unique(path)
            except:
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
                    'is_playlist': 'entries' in info or info.get('_type') == 'playlist',
                    'playlist_count': info.get('playlist_count') or (len(info['entries']) if 'entries' in info and isinstance(info['entries'], list) else None),
                    'webpage_url': info.get('webpage_url') or url,
                    'original_url': url,
                }
        except Exception as e:
            return {'error': str(e)}

    def download_video(self, url, options, progress_callback=None):
        """
        Downloads the video to a temp folder, merges it, and moves to final destination.
        """
        final_output_path = options.get('output_path', os.getcwd())
        
        # Create a temp directory inside the final output path to avoid cross-drive move issues
        temp_dir = os.path.join(final_output_path, ".temp_dl")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Base options
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else [],
            'noplaylist': True, 
            'ffmpeg_location': self.ffmpeg_location,
            'ignoreerrors': True,
            'overwrites': True, 
        }

        if options.get('is_playlist') or 'list=' in url:
            # Force playlist mode by explicitly using the playlist URL
            try:
                if 'list=' in url and 'youtube.com' in url: # Re-added simple safety check
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    if 'list' in qs:
                        playlist_id = qs['list'][0]
                        url = f"https://www.youtube.com/playlist?list={playlist_id}"
            except: pass

            ydl_opts['noplaylist'] = False
            # Playlist subfolder structure in temp: temp/.temp_dl/PlaylistName/
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(playlist_title)s', '%(title)s.%(ext)s')

        # Format selection (Same as before)
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
                     ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
                 else:
                     ydl_opts['format'] = f"bestvideo+bestaudio/best"

            ydl_opts['merge_output_format'] = ext
            
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': ext,
            }]
            ydl_opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']

        try:
            # Capture the filenames created to move them later
            # Since yt-dlp doesn't return the list easily without huge overhead,
            # we can rely on moving everything from temp_dir that isn't a partial file.
            
            with UniqueYoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Move files from temp to final
            # 1. Handle Playlist Folders
            for item in os.listdir(temp_dir):
                s = os.path.join(temp_dir, item)
                d = os.path.join(final_output_path, item)
                
                # If d exists and is file, make unique? 
                # Or simplistic move? 
                
                if os.path.isdir(s):
                    # It's a playlist folder, move content or folder?
                    # Move entire folder. If exists, merge? 
                    # shutil.move fails if exists.
                    if not os.path.exists(d):
                        shutil.move(s, d)
                    else:
                        # Move inner files
                        for inner in os.listdir(s):
                            shutil.move(os.path.join(s, inner), os.path.join(d, inner))
                        shutil.rmtree(s) # delete empty folder
                else:
                    # It's a video file
                    if not item.endswith(".part") and not item.endswith(".ytdl"):
                        # Ensure unique name in destination
                         final_name = make_unique(d)
                         shutil.move(s, final_name)
            
            # Cleanup temp dir if empty
            try: os.rmdir(temp_dir)
            except: pass # might not be empty if failed files
            
            return "Success"
        except Exception as e:
            return str(e)

# Example usage for testing
if __name__ == "__main__":
    dl = YoutubeDownloader()
    # print(dl.get_info("..."))
