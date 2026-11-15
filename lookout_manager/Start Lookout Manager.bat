@echo off
REM === Lookout Manager ===
setlocal
set "PYEXE=py -3"
where py >nul 2>nul || set "PYEXE=python"
%PYEXE% --version >nul 2>nul
if errorlevel 1 (
  echo Python 3 was not found. Install it from python.org and tick "Add to PATH".
  pause ^& exit /b
)
%PYEXE% -c "import paramiko" >nul 2>nul
if errorlevel 1 (
  echo Installing the SSH helper the setup tab needs, one time please wait...
  %PYEXE% -m pip install paramiko
)
%PYEXE% -c "import paramiko" >nul 2>nul
if errorlevel 1 (
  echo Could not install paramiko automatically. Run this once:  %PYEXE% -m pip install paramiko
  pause ^& exit /b
)
start "" %PYEXE% "%~dp0System Files\lookout_manager.py"
endlocal
