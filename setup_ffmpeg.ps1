$url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zip = "ffmpeg.zip"
$dest = "ffmpeg_temp"

Write-Host "Downloading FFmpeg..."
Invoke-WebRequest -Uri $url -OutFile $zip

Write-Host "Extracting FFmpeg..."
Expand-Archive -Path $zip -DestinationPath $dest -Force

Write-Host "Locating binaries..."
$binPath = Get-ChildItem -Path $dest -Recurse -Filter "ffmpeg.exe" | Select-Object -ExpandProperty DirectoryName

Write-Host "Moving binaries to project root..."
Move-Item -Path "$binPath\ffmpeg.exe" -Destination . -Force
Move-Item -Path "$binPath\ffprobe.exe" -Destination . -Force

Write-Host "Cleaning up..."
Remove-Item $zip -Force
Remove-Item $dest -Recurse -Force

Write-Host "FFmpeg setup complete!"
