@echo off
cd /d %~dp0
poetry install --no-interaction
poetry run pyinstaller --onefile --name appDataMove src/main.py
