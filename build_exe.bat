@echo off
echo Installing requirements...
py -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo "py command failed, trying python..."
    python -m pip install -r requirements.txt
)

echo Building EXE v2.0...
py -m PyInstaller --noconsole --onefile --name "YoutubeDownloader_v2.0" --icon=app_icon.ico --add-data "themes;themes" --add-data "app_icon.ico;." --add-binary "ffmpeg.exe;." --distpath "%USERPROFILE%\Downloads" main.py
if %errorlevel% neq 0 (
    echo "py command failed, trying python..."
    python -m PyInstaller --noconsole --onefile --name "YoutubeDownloader_v2.0" --icon=app_icon.ico --add-data "themes;themes" --add-data "app_icon.ico;." --add-binary "ffmpeg.exe;." --distpath "%USERPROFILE%\Downloads" main.py
)

echo Build Complete! EXE saved to Downloads folder.

