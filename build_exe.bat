@echo off
echo Installing requirements...
py -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo "py command failed, trying python..."
    python -m pip install -r requirements.txt
)

echo Building EXE...
py -m PyInstaller --noconsole --onefile --name "YoutubeDownloader" --icon=NONE main.py
if %errorlevel% neq 0 (
    echo "py command failed, trying python..."
    python -m PyInstaller --noconsole --onefile --name "YoutubeDownloader" --icon=NONE main.py
)

echo Build Complete! Look in the 'dist' folder.
pause
