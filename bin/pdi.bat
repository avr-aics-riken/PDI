@echo off

set DRVNAME=%~d0
set DIRNAME=%~p0
rem echo "%DRVNAME%%DIRNAME%"

rem set PDI_LOG_FILENAME=%DRVNAME%%DIRNAME%\..\logs\pdi_%USERNAME%.log

python -B "%DRVNAME%%DIRNAME%\..\lib\python\pdi.py" %1 %2 %3 %4 %5 %6 %7 %8 %9

rem pause
