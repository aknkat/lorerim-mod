@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect-LoadingScreenDiagnostics.ps1"
if errorlevel 1 echo Diagnostic failed. Copy the error text and send it.
pause
