# Modern YouTube Downloader by Legendnoobe

A sleek, modern, and powerful YouTube Downloader application for Windows. Built with Python, CustomTkinter, and yt-dlp.

![App Icon](app_icon.ico)

## Features

- **Modern UI**: Clean, dark-themed interface using CustomTkinter.
- **Auto-Rename**: Automatically handles duplicate filenames by adhering to Windows standards (e.g., `Video (1).mp4`).
- **Format Support**: Download primarily in **MP4** (Video) or **MP3** (Audio).
- **Quality Options**: Choose from 8K down to 240p for video, or high-quality variable bitrates for audio.
- **Playlist Support**: Fully supports downloading entire playlists into organized subfolders.
- **Shorts Support**: Seamlessly downloads YouTube Shorts.
- **Queue System**: Add multiple videos to a queue and download them sequentially.
- **Completed Tab**: Review your download history and open files directly from the app.
- **Theming**: "Dark" and "Light" modes with a variety of accent colors.
- **Localization**: Full support for **English** and **Turkish** languages.
- **Portable**: Single executable file with no installation required.

## Installation

No installation is necessary!

1. Download the latest `ModernYoutubeDownloader.exe` release.
2. Double-click to run.
3. Requires **Windows 10/11**.

## Usage

1. **Paste Link**: Copy a YouTube video or playlist URL and paste it into the input box.
2. **Add to Queue**: Click the **+** button.
3. **Customize**: 
   - Select **Video** or **Audio**.
   - Choose your desired **Resolution** or **Audio Quality**.
4. **Download**: Click **Start Download All**.
5. **Finish**: Once complete, find your files in the `Downloads` folder (or your custom selected path).

## Requirements (for Developers)

If you wish to run the source code directly:

- Python 3.10+
- `customtkinter`
- `yt-dlp`
- `Pillow`
- `ffmpeg` (must be in system PATH or root directory)

```bash
pip install customtkinter yt-dlp Pillow
```

## Build

To build the executable yourself using PyInstaller:

```bash
py -m PyInstaller --noconfirm --onefile --windowed --name "ModernYoutubeDownloader" --icon "app_icon.ico" --add-data "themes;themes" --add-data "app_icon.ico;." --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." main.py
```

## Credits
-Icon link https://share.google/s3dgealX7uCYygT1G

- **Developer**: Legendnoobe
- **Libraries**: CustomTkinter, yt-dlp
