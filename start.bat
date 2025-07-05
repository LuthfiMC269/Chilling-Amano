@echo off
set VENV_PATH=.venv
set SCRIPT_PATH=bot.py

call %VENV_PATH%\Scripts\activate.bat

python %SCRIPT_PATH%
pause
