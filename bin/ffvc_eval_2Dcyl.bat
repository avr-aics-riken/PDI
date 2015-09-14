@echo off

set DRVNAME=%~d0
set DIRNAME=%~p0
rem echo "%DRVNAME%%DIRNAME%"

rem set PDI_LOG_FILENAME=%DRVNAME%%DIRNAME%\..\logs\pdi_%USERNAME%.log

if exist "%DRVNAME%%DIRNAME%..¥lib¥python\dist¥ffvc_eval_2Dcyl.exe" (
   "%DRVNAME%%DIRNAME%..\lib\python\dist¥ffvc_eval_2Dcyl.exe" %*
) else (
  python -B "%DRVNAME%%DIRNAME%..\lib\python\ffvc_eval_2Dcyl.py" %*
)

rem pause
