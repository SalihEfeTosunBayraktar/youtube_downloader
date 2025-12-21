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
            'noplaylist': True, # Default to single video unless playlist requested, handling playlists needs different logic usually
            'ffmpeg_location': self.ydl_opts.get('ffmpeg_location'),
        }

        if options.get('is_playlist'):
            ydl_opts['noplaylist'] = False
            ydl_opts['outtmpl'] = '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'

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
            # Simple quality selection logic
            audio_selection = 'bestaudio[ext=m4a]' if target_ext == 'mp4' else 'bestaudio'
            
            if options.get('quality') == 'best':
                ydl_opts['format'] = f'bestvideo+{audio_selection}/best'
            else:
                # Try to target height if possible, else best
                # This is a basic implementation. Robust format selection is complex.
                res = options.get('quality', '').replace('p', '')
                if res.isdigit():
                    ydl_opts['format'] = f'bestvideo[height<={res}]+{audio_selection}/best[height<={res}]'
                else:
                    ydl_opts['format'] = f'bestvideo+{audio_selection}/best'
            
            ydl_opts['merge_output_format'] = target_ext

        # Prepare YDL options specifically to resolve filename first
        # We need to know the potential filename to check for conflicts
        # This requires fetching info first
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Determine final extension and basic filename
            # Note: prepare_filename might return the temp file (e.g. .webm before .mp4 merge)
            # We want to check the FINAL file existence.
            
            title = info.get('title', 'video')
            # Sanitize title simply or let ydl do it? 
            # We will use ydl's sanitize_filename loosely or manually
            title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
            
            final_ext = target_ext
            
            base_filename = title
            counter = 1
            
            # loop to find unique name
            while True:
                if counter == 1:
                    candidate_name = f"{base_filename}.{final_ext}"
                else:
                    candidate_name = f"{base_filename} ({counter}).{final_ext}"
                
                full_path = os.path.join(output_path, candidate_name)
                if not os.path.exists(full_path):
                    # Found unique name
                    # We must provide this exact path to yt-dlp as outtmpl
                    # However, we must strip extension for outtmpl if we want ydl to handle extension?
                    # No, simply providing the full path (minus extension if ydl adds it, or with it?)
                    # Best way: provide outtmpl with the chosen NAME but let YDL handle extension placeholders if needed?
                    # BUT we want to enforce THIS name.
                    # Since we are merging/converting, ydl might use intermediate files.
                    # If we set outtmpl to 'C:/path/to/file (1)', and let extension be %(ext)s, 
                    # ydl might create 'file (1).webm' then merge to 'file (1).mp4'.
                    # This matches our expectation.
                    
                    name_without_ext = os.path.splitext(candidate_name)[0]
                    ydl_opts['outtmpl'] = os.path.join(output_path, f"{name_without_ext}.%(ext)s")
                    break
                counter += 1

            # Determine quality again just in case (code duplication avoided by not changing earlier logic much)
            # Now download with the specific outtmpl
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return "Success"
        except Exception as e:
            return str(e)

# Example usage for testing
if __name__ == "__main__":
    dl = YoutubeDownloader()
    # print(dl.get_info("..."))
