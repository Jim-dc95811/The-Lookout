@echo off
REM === Lookout Alias Manager ===
set "PYEXE=py -3"
where py >nul 2>nul || set "PYEXE=python"
%PYEXE% --version >nul 2>nul || (echo Python 3 was not found. Install it from python.org, tick "Add to PATH". & pause & exit /b)
start "" %PYEXE% "%~dp0System Files\alias_manager.py"
