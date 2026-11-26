# -*- mode: python ; coding: utf-8 -*-


import os
import re

block_cipher = None

# 版本号直接读 Watermelon.py 里的 VERSION，免得两处不一致
# （一键更新靠 app 的 CFBundleShortVersionString 判断新旧，必须和代码里的 VERSION 一样）
with open(os.path.join(SPECPATH, 'Watermelon.py'), encoding='utf-8') as _src:
    __version__ = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', _src.read(), re.M).group(1)

# 2.2.4 起（2026-11-20）：
# - 程序标识 com.ryanthehito.watermelon（和 Broccoli / Strawberry / Tomato / Raspberry 同一套；原来是 "Watermelon"）。
#   一键更新只认这个标识 + 同一开发者签名（Watermelon.py 里的 WATERMELON_UPDATE_BUNDLE_ID），两处必须一样。
#   装着 2.2.3 的人要手动装一次这一版，之后才能一键更新。
# - 程序分成几个文件（放在这个 spec 旁边）：glass_kit / smooth_widgets / watermelon_ui（液态玻璃界面）、
#   watermelon_office + office_editor_bridge（Word / Excel / PowerPoint）、watermelon_notes（备忘录互通）、
#   markdown_preview（预览）。
# - 带进 app 的文件夹：i18n（中日文）、office_editor（Office 编辑组件，约 510 MB，AGPL-3.0，里面有它的 LICENSE）、
#   MathJax-2.7.9（公式引擎，约 30 MB，不联网；2026-11-25 从 2.7.1 升上来）。
# 2026-11-25 起：MCP 工具（watermelon_tools + 各 App 共用的 app_mcp_host）：别的 AI 软件用同一个可执行文件
#   加 --mcp-stdio 参数来操作 Watermelon（Contents/MacOS/Watermelon --mcp-stdio）；不是另一个要签名的程序。
# - 不带 Dock 图标启动（LSBackgroundOnly），运行时再显示（菜单栏菜单 › 👀 Show/Hide dock icon；默认显示）。
# - fs.txt / lastused.txt / text_position.txt 只是默认值：第一次启动时复制到
#   ~/Library/Application Support/com.ryanthehito.watermelon/Resources，之后 app 包里不再写任何东西。
MODULES = ['glass_kit', 'smooth_widgets', 'watermelon_ui', 'watermelon_office', 'office_editor_bridge',
           'watermelon_notes', 'markdown_preview', 'watermelon_attachments', 'watermelon_broccoli',
           'watermelon_lecture', 'watermelon_courseware', 'watermelon_outline', 'watermelon_handles',
           'watermelon_scan', 'watermelon_anki', 'watermelon_marks', 'watermelon_tools', 'app_mcp_host',
           'broccoli_write_back']   # 2026-11-25 Write Here with Broccoli (the same file as Strawberry's)
FILES = ['wtmenu.icns', 'wtmdsk.icns', 'wtmenu.png', 'wechat50.png', 'wechat20.png', 'wechat10.png', 'wechat5.png',
         'alipay50.png', 'alipay20.png', 'alipay10.png', 'alipay5.png', 'bottom7.png', 'middle6.png', 'middle2.png',
         'set2.png', 'fs.txt', 'lastused.txt', 'chillduanheisong_widelight.otf', 'text_position.txt', 'repeat.png',
         'repeat2.png', 'speaker.png', 'return.wav', 'normal.wav', 'delete.wav', 'bell.mp3']
FOLDERS = ['i18n', 'office_editor', 'MathJax-2.7.9']
REQUIRED_INSIDE = ['i18n/watermelon_zh_CN.qm', 'i18n/watermelon_ja_JP.qm', 'office_editor/manifest.json',
                   'office_editor/site/editor.html', 'office_editor/LICENSE.txt', 'MathJax-2.7.9/MathJax.js',
                   'MathJax-2.7.9/LICENSE']
JIEBA = '/Users/ryanshen/Documents/A-workingfilewithp3.11/.venv/lib/python3.11/site-packages/jieba'

# 缺一个文件就停：缺了也能打出包，但装上以后才发现没有中文 / 打不开 Word / 公式排不出来
_missing = [name for name in [m + '.py' for m in MODULES] + FILES + REQUIRED_INSIDE
            if not os.path.exists(os.path.join(SPECPATH, name))]
if not os.path.isdir(JIEBA):
    _missing.append(JIEBA)
if _missing:
    raise SystemExit('Watermelon.spec: missing: ' + ', '.join(_missing))

# 网页引擎在“打包用的环境”里多出来的假版本（和 Broccoli.spec / Tomato.spec 同一段，2026-11-25 加）。
# 从源码跑过带网页的程序后，环境里的 PyQt6 会多出一个空的 QtWebEngineCore.framework/Versions/Resources。
# PyInstaller 把 Versions/ 里排在最后的名字当成版本——“Resources”排在“A”后面——于是网页引擎的小程序被放到
# Versions/Resources 下面，而框架的链接指的是 Versions/A：打出来的 App 整体签名校验不过
# （embedded framework contains modified or invalid version），网页 / 预览 / Office 也起不来。
# 空的多余文件夹在分析前删掉；不是空的就停下来。
from pathlib import Path
import PyQt6 as _pyqt6
_webengine_versions = Path(_pyqt6.__file__).parent / 'Qt6' / 'lib' / 'QtWebEngineCore.framework' / 'Versions'
if _webengine_versions.is_dir():
    for _entry in sorted(_webengine_versions.iterdir()):
        if _entry.name != 'Current' and _entry.is_dir() and not _entry.is_symlink() and not any(_entry.iterdir()):
            _entry.rmdir()
            print('Removed an empty stray QtWebEngine version folder from the build environment:', _entry)
    _versions_left = sorted(e.name for e in _webengine_versions.iterdir() if e.name != 'Current')
    if len(_versions_left) != 1:
        raise SystemExit(f'Watermelon.spec: {_webengine_versions} holds {_versions_left}, not one version: PyInstaller '
                         'would package QtWebEngine under the last one. Remove the one that is not part of PyQt6 '
                         '(PyQt6 ships "A") and build again.')

a = Analysis(
    ['Watermelon.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[(name, '.') for name in FILES] + [(name, name) for name in FOLDERS] + [(JIEBA, 'jieba')],
    hiddenimports=['subprocess', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets',
                   'sqlite3', 'Quartz', 'Vision', 'CoreText', 'PyQt6.QtMultimedia'] + MODULES,   # Quartz：截图合成 PDF 用系统的 PDFKit
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 2026-11-25：Watermelon 只用 matplotlib 列字体名，但 matplotlib 里“装了就顺手用”的导入会把共用 .venv 里的
    # pandas → scipy → torch → transformers / opencv / onnxruntime 一路拖进来（试打包多了约 700 MB）。都用不到，排除。
    # 排除后 matplotlib.font_manager 照样列出全部字体（实测 647 种）。
    excludes=['torch', 'functorch', 'transformers', 'tokenizers', 'hf_xet', 'cv2', 'onnxruntime', 'scipy', 'pandas',
              'networkx', 'sympy', 'sklearn', 'tensorflow', 'IPython'],
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
    # 一键更新只认这个标识且同一开发者签名的新版本（WATERMELON_UPDATE_BUNDLE_ID），两处必须一样
    bundle_identifier='com.ryanthehito.watermelon',
    version=__version__,
    info_plist={
        # 和 Broccoli / Strawberry / Tomato 一样：不带 Dock 图标启动，运行时再显示或隐藏
        'LSBackgroundOnly': True,
        'NSHighResolutionCapable': True,
        # Watermelon 第一次向“备忘录”发指令时系统显示的说明
        'NSAppleEventsUsageDescription': 'Watermelon reads and writes the notes you open in its Notes mode.',
        # 用摄像头拍文件（听课模式 › 相机右键 › Take Photo with Camera…）时系统显示的说明；没有这一条，一开摄像头就被系统关掉
        'NSCameraUsageDescription': 'Watermelon uses the camera when you photograph paper as course material.',
    },
)
