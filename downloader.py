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
    
    # Check local directory or PATH
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
        
    return shutil.which('ffmpeg')

class YoutubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': os.path.dirname(get_ffmpeg_path()) if get_ffmpeg_path() else None
        }

    def get_info(self, url):
        """Fetches metadata for the given URL."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'is_playlist': 'entries' in info,
                    'webpage_url': info.get('webpage_url'),
                }
        except Exception as e:
            return {'error': str(e)}

    def download_video(self, url, options, progress_callback=None):
        """
        Downloads the video with specified options.
        options: {
            'format_type': 'video' or 'audio',
            'quality': '1080p', 'best', 'worst', '128', etc. [Not fully strictly implemented mapping yet, using best/worst for simplicity first]
            'ext': 'mp4', 'mkv', 'mp3'
        }
        """
        
        # Base options
        output_path = options.get('output_path', os.getcwd())
        
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else [],
            'noplaylist': True, 
            'ffmpeg_location': self.ydl_opts.get('ffmpeg_location'),
            'ignoreerrors': True, # Critical for playlists to keep going
        }

        if options.get('is_playlist'):
            ydl_opts['noplaylist'] = False
            # Fix: Ensure the directory structure is joined correctly with output_path
            # outtmpl becomes: download_path/PlaylistName/Index - Title.ext
            ydl_opts['outtmpl'] = os.path.join(output_path, '%(playlist_title)s', '%(playlist_index)s - %(title)s.%(ext)s')
        else:
            # Check duplicate filename for single video
            # (Keep existing duplicate logic for single videos)
            pass 

        # We need to apply duplicate logic only for non-playlists or complex playlists?
        # For playlists, yt-dlp handles overwrites usually, but let's leave it to yt-dlp for now to avoid complex pre-fetching of every item.
        
        format_type = options.get('format_type', 'video')
        target_ext = options.get('ext', 'mp4')

        if format_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': target_ext,
                'preferredquality': options.get('quality', '192'),
            }]
        else:
            # Video
            audio_selection = 'bestaudio[ext=m4a]' if target_ext == 'mp4' else 'bestaudio'
            if options.get('quality') == 'best':
                ydl_opts['format'] = f'bestvideo+{audio_selection}/best'
            else:
                res = options.get('quality', '').replace('p', '')
                if res.isdigit():
                    ydl_opts['format'] = f'bestvideo[height<={res}]+{audio_selection}/best[height<={res}]'
                else:
                    ydl_opts['format'] = f'bestvideo+{audio_selection}/best'
            
            ydl_opts['merge_output_format'] = target_ext

        # Only Run Duplicate Logic for Single Videos (Not Playlists)
        if not options.get('is_playlist'):
             try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                title = info.get('title', 'video')
                # Basic sanitize
                title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
                final_ext = target_ext
                base_filename = title
                counter = 1
                
                while True:
                    if counter == 1: candidate = f"{base_filename}.{final_ext}"
                    else: candidate = f"{base_filename} ({counter}).{final_ext}"
                    
                    if not os.path.exists(os.path.join(output_path, candidate)):
                        # Valid unique name
                        name_no_ext = os.path.splitext(candidate)[0]
                        ydl_opts['outtmpl'] = os.path.join(output_path, f"{name_no_ext}.%(ext)s")
                        break
                    counter += 1
             except:
                 pass # Fallback to default behavior if extraction fails

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return "Success"
        except Exception as e:
            return str(e)

# Example usage for testing
if __name__ == "__main__":
    dl = YoutubeDownloader()
    # print(dl.get_info("..."))
