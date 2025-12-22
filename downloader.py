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

def parse_time(t_str):
    if not t_str: return None
    try:
        parts = t_str.strip().split(':')
        parts = [float(p) for p in parts]
        if len(parts) == 1: return parts[0]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        return None
    except: return None

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
        temp_dir = os.path.join(final_output_path, "YMVD.temp_dl")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Base options
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else [],
            'noplaylist': True, 
            'ffmpeg_location': self.ffmpeg_location,
            'ignoreerrors': False,
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

        # Format selection
        if options.get('format_type') == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('ext', 'mp3'),
                'preferredquality': options.get('quality', '192'),
            }]
        elif options.get('format_type') == 'thumbnail':
            # Manual thumbnail download and processing
            try:
                # 1. Get info to find thumbnail URL
                # We often already have info, but to be safe or if direct download called:
                # Actually, this method is called inside a flow.
                # Use yt-dlp to extract info WITHOUT downloading anything first
                
                # If we are here, 'url' is the video URL.
                with yt_dlp.YoutubeDL({'quiet':True, 'skip_download':True}) as ydl:
                     info = ydl.extract_info(url, download=False)
                
                thumb_url = info.get('thumbnail')
                title = info.get('title', 'thumbnail')
                
                if not thumb_url:
                    return "Error: No thumbnail found"
                
                # 2. Download Image Data
                import urllib.request
                from PIL import Image
                import io
                
                # User selected format and quality
                target_ext = options.get('ext', 'jpg')
                quality_setting = options.get('quality', 'Original') # Original, 1080p, 720p...
                
                # Download
                req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    img_data = response.read()
                
                img = Image.open(io.BytesIO(img_data))
                
                # 3. Resize if needed
                if quality_setting != "Original":
                    # Parse target height
                    try:
                        target_h = int(quality_setting.replace('p', ''))
                        # Calculate width to maintain aspect ratio
                        # w / h = ar  => w = ar * h
                        aspect_ratio = img.width / img.height
                        target_w = int(aspect_ratio * target_h)
                        
                        # High quality resize
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    except:
                        pass # Fail silently to Original
                
                # 4. Save
                # Handle unique filename manually since we are bypassing yt-dlp download
                # output_path key in options includes the path provided by user.
                # wait, ydl_opts below sets outtmpl.
                # We need to respect the directory structure (temp dir).
                
                # Re-using the temp_dir logic from the function scope?
                # The function variables 'temp_dir' and 'final_output_path' are available if we are inside the method.
                # Yes, we are replacing the elif block inside 'download_video'.
                
                filename_base = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
                save_path = os.path.join(temp_dir, f"{filename_base}.{target_ext}")
                
                # Convert mode if needed (e.g. RGBA to RGB for jpg)
                if target_ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                img.save(save_path)
                
                # Do NOT return "Success" here; let it fall through to the move logic below
                # return "Success" 
                
            except Exception as e:
                return f"Thumbnail Error: {str(e)}"
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

        # Advanced Options: Playlist Range & trimming
        pl_start = options.get('playlist_start')
        pl_end = options.get('playlist_end')
        if (pl_start or pl_end) and (options.get('is_playlist') or 'list=' in url):
             s = pl_start if pl_start else ""
             e = pl_end if pl_end else ""
             ydl_opts['playlist_items'] = f"{s}-{e}"

        t_start = options.get('trim_start')
        t_end = options.get('trim_end')
        if (t_start or t_end) and options.get('format_type') != 'thumbnail':
             from yt_dlp.utils import download_range_func
             ts = parse_time(t_start)
             te = parse_time(t_end)
             if ts is not None or te is not None:
                 ydl_opts['download_ranges'] = download_range_func(None, [(ts, te)])
                 ydl_opts['force_keyframes_at_cuts'] = True

        try:
            # Capture the filenames created to move them later
            # Since yt-dlp doesn't return the list easily without huge overhead,
            # we can rely on moving everything from temp_dir that isn't a partial file.
            
            if options.get('format_type') != 'thumbnail':
                with UniqueYoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            # Cleanup temp dir if empty
            if not os.listdir(final_output_path) and not os.listdir(temp_dir):
                 # This check is tricky because files were moved.
                 pass

            # Check if we moved anything?
            # We can check if `seen_files` inside the caller was updated, but here we are in downloader.
            # Better: Check if `os.listdir(temp_dir)` had items BEFORE moving.
            
            # Refactoring the Move Logic to track count
            moved_count = 0
            # Move files from temp to final
            # 1. Handle Playlist Folders
            for item in os.listdir(temp_dir):
                moved_count += 1
                s = os.path.join(temp_dir, item)
                d = os.path.join(final_output_path, item)
                
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
            
            if moved_count == 0:
                return "Error: No files downloaded"
            
            return "Success"
        except Exception as e:
            return str(e)

# Example usage for testing
if __name__ == "__main__":
    dl = YoutubeDownloader()
    # print(dl.get_info("..."))
