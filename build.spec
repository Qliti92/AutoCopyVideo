# ============================================================
# BUILD SCRIPT - PyInstaller
# Chạy:  pyinstaller build.spec
# ============================================================
# Lưu ý: .env KHÔNG bundle vào .exe.
#         Đặt .env CÁ NH ÂN cạnh .exe sau khi build.
# ============================================================

import sys
import os

# Thư mục chứa build.spec (PyInstaller không có __file__ → dùng cwd)
HERE = os.path.abspath(os.getcwd())

a = Analysis(
    ['video_copy_tool.py'],
    pathex=[HERE],
    binaries=[],
    datas=[],                          # .env không bundle – user tự đặt cạnh .exe
    hiddenimports=[
        'dotenv',
        'colorama',
    ],
    excludes=[],
    norecursedirs=[],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='VideoCopyTool',
    debug=False,
    bootloader_argv=[],
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                      # Console app – không GUI
    # ── Icon ────────────────────────────────────
    # Đặt file icon.ico cạnh build.spec rồi uncomment dòng dưới:
    icon=os.path.join(HERE, 'icon.png'),
)
