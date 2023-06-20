import PyInstaller.__main__
from datetime import date

version = date.today().strftime('%Y%m%d')
name = 'NetBlocker'
PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--name',
    f'{name}-{version}'
])
