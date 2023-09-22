@echo off
pyinstaller --clean --onedir --noconsole --noconfirm --name "fire danger map generator" --icon "icon.png" --add-data "blank.png";"." --add-data "icon.png";"." "main.py"