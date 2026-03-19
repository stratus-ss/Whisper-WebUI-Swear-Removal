@echo off

call venv\scripts\activate

REM Set up CUDA library paths to include cuDNN
set CUDNN_PATH=%CD%\venv\Lib\site-packages\nvidia\cudnn\bin
set PATH=%CUDNN_PATH%;%PATH%

REM Suppress cuDNN debug logging
set CUDNN_LOGINFO_DBG=0
set CUDNN_LOGDEST_DBG=stderr

python app.py %*

echo "launching the app"
pause
