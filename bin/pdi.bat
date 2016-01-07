@echo off

set DRVNAME=%~d0
set DIRNAME=%~p0
rem echo "%DRVNAME%%DIRNAME%"

rem set PDI_LOG_FILENAME=%DRVNAME%%DIRNAME%\..\logs\pdi_%USERNAME%.log

if exist "%DRVNAME%%DIRNAME%..\lib\python\dist_%PROCESSOR_ARCHITECTURE%\pdi.exe" (
  "%DRVNAME%%DIRNAME%..\lib\python\dist_%PROCESSOR_ARCHITECTURE%\pdi.exe" %*
) else (
  if exist "%DRVNAME%%DIRNAME%..\lib\python\dist\pdi.exe" (
    "%DRVNAME%%DIRNAME%..\lib\python\dist\pdi.exe" %*
  ) else (
    python -B "%DRVNAME%%DIRNAME%..\lib\python\pdi.py" %*
  )
)

rem pause
