# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

__version__ = '2.1.0'

a = Analysis(
    ['Watermelon.py'],
    pathex=['/Users/ryanshenefield/Downloads/Watermelon.py'],
    binaries=[],
    datas=[('wtmenu.icns', '.'), ('wtmdsk.icns', '.'), ('wtmenu.png', '.'), ('wechat50.png', '.'), ('wechat20.png', '.'), ('wechat10.png', '.'), ('wechat5.png', '.'), ('alipay50.png', '.'), ('alipay20.png', '.'), ('alipay10.png', '.'), ('alipay5.png', '.'), ('bottom7.png', '.'), ('middle6.png', '.'), ('middle2.png', '.'), ('set2.png', '.'), ('/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/jieba', 'jieba'), ('fs.txt', '.'), ('lastused.txt', '.'), ('chillduanheisong_widelight.otf', '.'), ('text_position.txt', '.')],
    hiddenimports=['subprocess'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Watermelon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Watermelon',
)
app = BUNDLE(
    coll,
    name='Watermelon.app',
    icon='wtmdsk.icns',
    bundle_identifier=None,
    version=__version__,
)
