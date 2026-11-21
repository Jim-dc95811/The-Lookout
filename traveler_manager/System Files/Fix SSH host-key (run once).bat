@echo off
REM === One-time fix: stop the "REMOTE HOST IDENTIFICATION HAS CHANGED" error ===
REM === for the Traveler / Lookout box at 192.168.8.1. Run this once, ever.    ===
REM === Only needed if you SSH into the box by hand; the Manager never needs it. ===
setlocal

set "SSHDIR=%USERPROFILE%\.ssh"
set "CFG=%SSHDIR%\config"

if not exist "%SSHDIR%" mkdir "%SSHDIR%"

echo Clearing any old cached key for the box...
where ssh-keygen >nul 2>nul && ssh-keygen -R 192.168.8.1 >nul 2>nul

if exist "%CFG%" (
  findstr /i /c:"Host 192.168.8.1" "%CFG%" >nul 2>nul && goto already
)

(
  echo.
  echo Host 192.168.8.1
  echo     StrictHostKeyChecking no
  echo     UserKnownHostsFile NUL
  echo     CheckHostIP no
)>>"%CFG%"

echo.
echo ================================================================
echo  DONE - fixed for good.
echo.
echo  From now on, ssh root@192.168.8.1 connects with NO host-key
echo  warning, even after a factory reset or a firmware flash.
echo  You never have to run this again.
echo ================================================================
echo.
pause
exit /b

:already
echo.
echo ================================================================
echo  Already set up - the box is already in your SSH config.
echo  Nothing to do. The old cached key (if any) was just cleared.
echo ================================================================
echo.
pause
