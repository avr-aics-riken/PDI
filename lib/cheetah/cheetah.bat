@echo off
rem JAXA Cheeter moea program interface

set DRVNAME=%~d0
set DIRNAME=%~p0

"%DRVNAME%%DIRNAME%moea.%OS%.%PROCESSOR_ARCHITECTURE%.exe" %*

rem pause
