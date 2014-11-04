@echo off

set DRVNAME=%~d0
set DIRNAME=%~p0
rem echo "%DRVNAME%%DIRNAME%"

if "%1" == "" (
	echo usage: %~n0 param_descfile.pdi
	goto :EOF
)

set DRVNAME1=%~d1
set DIRNAME1=%~p1
set FILENAME=%~nx1
rem echo "%DRVNAME1%%DIRNAME1%%FILENAME%"

rem set PDI_LOG_FILENAME=%DRVNAME%%DIRNAME%\..\logs\pdi_%USERNAME%.log

cd "%DRVNAME1%%DIRNAME1%"
python "%DRVNAME%%DIRNAME%\..\lib\python\pdi.py" -d %FILENAME%

rem pause
