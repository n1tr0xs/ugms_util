@echo off
pyinstaller --clean --onedir --noconsole --noconfirm --icon "icon.png" --add-data "blank.png";"." --add-data "icon.png";"." "fire danger map generator.py"