@echo off
pyinstaller --clean --onedir --noconsole --noconfirm --name "fire danger map generator win7" --icon "icon.png" --add-data "blank.png";"." --add-data "icon.png";"." "main.py"