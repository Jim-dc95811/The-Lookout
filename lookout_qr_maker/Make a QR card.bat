@echo off
setlocal
title Lookout QR Maker
set "PYEXE=py -3"
where py >nul 2>nul || set "PYEXE=python"
%PYEXE% --version >nul 2>nul || (echo Python 3 was not found.  Install it from https://www.python.org/downloads/windows/ and tick "Add python.exe to PATH". & pause & exit /b 1)
%PYEXE% -c "import PIL" 2>nul || (echo First run: installing Pillow... & %PYEXE% -m pip install pillow)
%PYEXE% -c "import PIL" 2>nul || (echo Could not install Pillow.  Ask IT to run:  %PYEXE% -m pip install pillow & pause & exit /b 1)
%PYEXE% "%~dp0System Files\lookout_qr.py"
if errorlevel 1 pause
