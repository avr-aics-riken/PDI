@echo off

set DRVNAME=%~d0
set DIRNAME=%~p0
rem echo "%DRVNAME%%DIRNAME%"

rem set PDI_LOG_FILENAME=%DRVNAME%%DIRNAME%\..\logs\pdi_%USERNAME%.log

if exist "%DRVNAME%%DIRNAME%..¥lib¥python\dist¥xpdi_genparam.exe" (
   "%DRVNAME%%DIRNAME%..\lib\python\dist¥xpdi_genparam.exe" %*
) else (
  python -B "%DRVNAME%%DIRNAME%..\lib\python\xpdi_genparam.py" %*
)

rem pause
