@echo off
echo Starting VoxSketch services...

:: Start Landing Hub & Canvas Studio (Port 8002)
start "VoxSketch - Landing Hub (8002)" /D "%~dp0voxsketch-final-project\trail" cmd /k python -m http.server 8002

:: Start Voice to Sketch Generator (Port 5000)
start "VoxSketch - Generator (5000)" /D "%~dp0voxsketch-final-project\generate-sketch" cmd /k python app.py

:: Start Forensic Matcher (Port 5001)
start "VoxSketch - Matcher (5001)" /D "%~dp0voxsketch-final-project\databasematch" cmd /k python -X utf8 app.py

echo.
echo All services started in separate windows!
echo If any window closes or displays an error, keep it open to check the message.
echo.
pause
