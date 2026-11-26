#!/usr/local/bin/python3.11
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import sys
# Started by an AI app as its MCP server (the family's rules: APP_MCP_SPEC.md): no window, only the bridge that
# forwards to the tools of the apps on this Mac. Before anything else is imported or printed: stdout carries
# nothing but MCP messages.
if '--mcp-stdio' in sys.argv[1:]:
	import app_mcp_host
	sys.exit(app_mcp_host.main())

import base64
import codecs
import atexit
import hashlib
import plistlib
import shutil
import json
import html as html_lib
import tempfile
import traceback
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout,
							 QSystemTrayIcon, QMenu, QComboBox,
							 QMenuBar, QFileDialog, QLineEdit,
							 QSplitter, QTextEdit, QListWidget, QCheckBox, QSlider,
							 QFrame, QGraphicsDropShadowEffect, QDialog, QGraphicsOpacityEffect, QStackedWidget)
from PyQt6.QtCore import QFileSystemWatcher, Qt, QPropertyAnimation, QRect, QTimer, QThread, pyqtSignal, QSize, QEvent, QRectF, QEventLoop, pyqtSlot, QParallelAnimationGroup, QSequentialAnimationGroup, QEasingCurve, QPoint, QUrl, QObject, QMimeData
from PyQt6.QtGui import QInputMethodQueryEvent, QKeyEvent, QAction, QActionGroup, QIcon, QColor, QFontDatabase, QPixmap, QCursor, QGuiApplication, QPainter, QPen, QPainterPath, QPalette, QFont, QSurfaceFormat, QBrush, QLinearGradient, QImage, QMouseEvent, QRegion
import PyQt6.QtGui
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineDownloadRequest, QWebEngineScript
import sys
import webbrowser
import jieba
import re
import urllib3
import logging
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import html2text
import subprocess
import threading
import os
from pathlib import Path
import markdown2
from datetime import datetime
import matplotlib.font_manager
from PIL import Image, ImageQt, ImageFilter
import time
try:
	from AppKit import NSWorkspace, NSColor
except ImportError:
	NSWorkspace = None
	NSColor = None
try:
	from Foundation import NSUserDefaults, NSSelectorFromString, NSDistributedNotificationCenter, NSObject
	import objc
except Exception:
	NSUserDefaults = None
	NSSelectorFromString = None
	NSDistributedNotificationCenter = None
	NSObject = None
	objc = None

# QtWebEngine 无障碍崩溃规避（同 Broccoli）：macOS + Qt6 下 Chromium 在导航时会用空指针调用
# QAccessible::uniqueId 而闪退。关掉 Blink/渲染进程的无障碍树即可；必须在创建 QApplication 之前设置。
_existing_flags = os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS', '')
for _flag in ('--disable-blink-features=AccessibilityObjectModel', '--disable-renderer-accessibility'):
	if _flag not in _existing_flags:
		_existing_flags = (_existing_flags + ' ' + _flag).strip()
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = _existing_flags

# UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md
# 让 macOS 给这个程序画“新设计”（液态玻璃）的红绿灯、菜单、提醒（样式书 5.7.2）。系统按主程序是用哪年的
# 开发包编的来决定新款还是老款；Python 3.11 和打包启动程序记的都是旧的，所以要在建 QApplication 之前
# 声明（只在这次运行的内存里，不写进用户的设置）。
if sys.platform == 'darwin' and NSUserDefaults is not None:
	try:
		NSUserDefaults.standardUserDefaults().registerDefaults_(
			{'com.apple.SwiftUI.IgnoreSolariumLinkedOnCheck': True})
	except Exception:
		pass

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

def _watermelon_resource_path():
	"""图片、声音、字体从“正在运行的这个 app”里读（app 放在哪都行）；从源码运行时读装在“应用程序”里的那份。"""
	try:
		if getattr(sys, 'frozen', False):
			resources = os.path.normpath(os.path.join(os.path.dirname(sys.executable), '..', 'Resources'))
			if os.path.isfile(os.path.join(resources, 'bottom7.png')):
				return resources + '/'
	except Exception:
		pass
	return '/Applications/Watermelon.app/Contents/Resources/'


BasePath = _watermelon_resource_path()

VERSION = "2.2.4"
NAME = 'Watermelon'

# 程序标识和文件夹（2026-11-20，Ryan：“程序标识一定要改，改的和其他的是同一个格式的”“这个路径你也得需要帮我……
# 改到那个合适的路径里面去”——和 Broccoli / Strawberry / Tomato / Raspberry 同一套）：
#   标识 com.ryanthehito.watermelon（原来是 "Watermelon"）
#   ~/Library/Application Support/com.ryanthehito.watermelon/WatermelonAppPath   数据（原来 ~/WatermelonAppPath）
#   ~/Library/Application Support/com.ryanthehito.watermelon/Resources           设置（原来写在 app 包里）
#   ~/Library/Caches/com.ryanthehito.watermelon/                                  缓存（更新安装包、备忘录缓存）
# app 包里只读不写：每次更新整个 app 会被换掉。
WATERMELON_BUNDLE_ID = 'com.ryanthehito.watermelon'
LEGACY_WATERMELON_BUNDLE_ID = 'Watermelon'
LEGACY_WATERMELON_DATA_DIR = os.path.join(str(Path.home()), 'WatermelonAppPath')
WATERMELON_APPLICATION_SUPPORT_DIR = os.path.join(str(Path.home()), 'Library', 'Application Support', WATERMELON_BUNDLE_ID)
WATERMELON_DATA_DIR = os.path.join(WATERMELON_APPLICATION_SUPPORT_DIR, 'WatermelonAppPath')
WATERMELON_SETTINGS_DIR = os.path.join(WATERMELON_APPLICATION_SUPPORT_DIR, 'Resources')
WATERMELON_CACHE_ROOT = os.path.join(str(Path.home()), 'Library', 'Caches', WATERMELON_BUNDLE_ID)
WATERMELON_SETTINGS_FILES = ('fs.txt', 'lastused.txt', 'bg_color.txt', 'always_on_top.txt',
							 'text_position.txt', 'notes_cache.json')


def _data_folder_entries(folder):
	try:
		return [name for name in os.listdir(folder) if name != '.DS_Store']
	except OSError:
		return []


def _real_folder(path):
	return os.path.isdir(path) and not os.path.islink(path)


def _other_watermelon_running():
	"""另一个 Watermelon 正开着（旧版本还在往 ~/WatermelonAppPath 里写）。"""
	try:
		from AppKit import NSRunningApplication
		mine = os.getpid()
		return any(int(running.processIdentifier()) != mine
				   for bundle_id in (LEGACY_WATERMELON_BUNDLE_ID, WATERMELON_BUNDLE_ID)
				   for running in NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle_id))
	except Exception:
		return False


def _move_legacy_data_folder():
	"""'latest'（旧位置没有东西）/ 'moved'（整个文件夹改名搬过去，里面每个文件的相对位置不变）/ 'busy'（另一个
	Watermelon 开着：这次仍用旧文件夹，下次启动再搬）/ 'linked'（~/WatermelonAppPath 是用户自己做的链接：照用）/
	'set_aside'（搬完以后旧位置又被旧版本建了一个：收进数据文件夹的 Backups，不合并）/ 'error'（这次用旧的，
	下次再试）。照 Tomato 2026-11-17 的写法。"""
	global WATERMELON_DATA_DIR
	old_data, new_data = LEGACY_WATERMELON_DATA_DIR, WATERMELON_DATA_DIR
	if os.path.islink(old_data):
		if not _data_folder_entries(new_data):
			WATERMELON_DATA_DIR = old_data
			return 'linked'
		return 'latest'
	if not _real_folder(old_data):
		return 'latest'
	if _other_watermelon_running():
		WATERMELON_DATA_DIR = old_data
		return 'busy'
	try:
		if _data_folder_entries(new_data):
			aside = os.path.join(new_data, 'Backups', 'WatermelonAppPath-' + time.strftime('%Y%m%d-%H%M%S'))
			os.makedirs(os.path.dirname(aside), exist_ok=True)
			os.rename(old_data, aside)
			logging.warning('A data folder was made at %s again; it was put into %s.', old_data, aside)
			return 'set_aside'
		os.makedirs(os.path.dirname(new_data), exist_ok=True)
		if os.path.isdir(new_data):
			shutil.rmtree(new_data)   # 空的（最多有访达的 .DS_Store）
		os.rename(old_data, new_data)
		return 'moved'
	except OSError:
		logging.exception('Moving the data folder %s to %s failed.', old_data, new_data)
		if _real_folder(old_data) and not _data_folder_entries(new_data):
			WATERMELON_DATA_DIR = old_data
			return 'error'
		return 'latest'


def _repoint_file_list(data_dir, old_dir=None):
	"""文件列表 DoNotDelete.txt 每行是“名字||完整路径”。数据文件夹搬走后，指向旧文件夹里面的路径改成新文件夹；
	指向别处（iCloud、Obsidian……）的不动。返回改了几行。"""
	old_dir = (old_dir or LEGACY_WATERMELON_DATA_DIR).rstrip('/')
	if os.path.normpath(data_dir) == os.path.normpath(old_dir):
		return 0
	list_path = os.path.join(data_dir, 'DoNotDelete.txt')
	try:
		with open(list_path, 'r', encoding='utf-8') as handle:
			lines = handle.read().split('\n')
	except OSError:
		return 0
	changed = 0
	for index, line in enumerate(lines):
		title, sep, path = line.partition('||')
		if sep and (path == old_dir or path.startswith(old_dir + '/')):
			lines[index] = title + sep + data_dir.rstrip('/') + path[len(old_dir):]
			changed += 1
	if changed:
		try:
			temp_path = list_path + '.tmp'
			with open(temp_path, 'w', encoding='utf-8') as handle:
				handle.write('\n'.join(lines))
			os.replace(temp_path, list_path)
		except OSError:
			logging.exception('Rewriting the file list failed.')
			return 0
	return changed


def _seed_settings_folder(settings_dir, app_resources):
	"""设置以前写在 app 包里。设置文件夹里还没有的那几个文件，从 app 包里拿一份（旧版本留下的值，或者安装包
	带的默认值）；已经有的不碰。"""
	copied = []
	try:
		os.makedirs(settings_dir, exist_ok=True)
	except OSError:
		logging.exception('Making the settings folder failed.')
		return copied
	for name in WATERMELON_SETTINGS_FILES:
		target = os.path.join(settings_dir, name)
		source = os.path.join(app_resources, name)
		if os.path.exists(target) or not os.path.isfile(source):
			continue
		try:
			shutil.copy2(source, target)
			copied.append(name)
		except OSError:
			logging.exception('Copying the setting %s failed.', name)
	return copied


def _move_legacy_caches(cache_root):
	"""备忘录缓存 ~/Library/Caches/NotesMarkdown 搬进新的缓存文件夹；旧的更新下载文件夹直接删（都是能重新
	下载的安装包）。"""
	caches = os.path.join(str(Path.home()), 'Library', 'Caches')
	try:
		os.makedirs(cache_root, exist_ok=True)
		old_notes, new_notes = os.path.join(caches, 'NotesMarkdown'), os.path.join(cache_root, 'NotesMarkdown')
		if _real_folder(old_notes) and not os.path.exists(new_notes):
			os.rename(old_notes, new_notes)
		old_updates = os.path.join(caches, 'Watermelon')
		if _real_folder(old_updates):
			shutil.rmtree(old_updates, ignore_errors=True)
	except OSError:
		logging.exception('Moving the caches failed.')


def carry_over_macos_preferences(old_domain=LEGACY_WATERMELON_BUNDLE_ID, new_domain=WATERMELON_BUNDLE_ID, *,
								 only_in_app=True, defaults=None):
	"""macOS 按程序标识记这个 app 自己的状态（菜单栏图标的位置、打开文件面板上次的文件夹）。换了标识的 app
	接过旧标识的那些（自己已经设的不覆盖），旧的清空。只在打包好的 app 里做（从源码运行时那是 Python 的）。
	返回接过来几项。（Broccoli / Strawberry / Tomato 的写法。）"""
	try:
		if only_in_app:
			from Foundation import NSBundle
			if str(NSBundle.mainBundle().bundleIdentifier() or '') != new_domain:
				return 0
		if defaults is None:
			defaults = NSUserDefaults.standardUserDefaults()
		old = defaults.persistentDomainForName_(old_domain)
		if not old:
			return 0
		current = defaults.persistentDomainForName_(new_domain) or {}
		merged = dict(old)
		merged.update(dict(current))
		defaults.setPersistentDomain_forName_(merged, new_domain)
		defaults.removePersistentDomainForName_(old_domain)
		return len(set(dict(old)) - set(dict(current)))
	except Exception:
		logging.exception('Carrying the macOS preferences over to %s failed.', new_domain)
		return 0


os.makedirs(WATERMELON_APPLICATION_SUPPORT_DIR, exist_ok=True)
DATA_FOLDER_MOVE_REPORT = _move_legacy_data_folder()
os.makedirs(WATERMELON_DATA_DIR, exist_ok=True)
FILE_LIST_LINES_REPOINTED = _repoint_file_list(WATERMELON_DATA_DIR)
_seed_settings_folder(WATERMELON_SETTINGS_DIR, BasePath)
_move_legacy_caches(WATERMELON_CACHE_ROOT)
MACOS_PREFERENCES_CARRIED_OVER = carry_over_macos_preferences()
SettingsPath = WATERMELON_SETTINGS_DIR + '/'   # 设置文件（字号、字体、背景色、置顶、文字位置、备忘录缓存）

os.environ["QT_QUICK_BACKEND"] = "metal"

fmt = QSurfaceFormat()
fmt.setSamples(8)  # 打开 MSAA 多重采样抗锯齿
QSurfaceFormat.setDefaultFormat(fmt)

# ══ 液态玻璃界面（2026-11-20，样式书 UI_STYLEBOOK_macOS27.md 第 5.14 节）══════════════════════════
# 玻璃组件 glass_kit.py（从 Broccoli 经 Strawberry / Tomato / Raspberry 原样复制）和 Watermelon 自己
# 搭在它上面的 watermelon_ui.py 放在这个文件旁边；两个都要等 QApplication 建好才能导入。
# - 主窗口：透明画布 + 打字机底图 + 编辑区（内容，永远不是玻璃），样子不变；
# - 打字机上的圆形按钮、网页标签栏、白色胶囊按钮 = 系统玻璃；打字机上的深灰按钮、下拉保持灰色；
# - 下拉的弹出、右键菜单 = 系统菜单；提醒 / 询问 = 系统提醒；
# - About / 更新 / 捐赠 / 设置 = 系统红绿灯 + 窗口玻璃；备忘录选择 = 玻璃对话框。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glass_kit
import watermelon_ui
from glass_kit import (_tr, MacNormalButton, WhiteButton, DropdownButton, glass_button,
					   style_broccoli_context_menu, use_native_web_context_menu, add_search_glyph,
					   glass_search_field, keep_scroll_bar_knob, attach_inwindow_liquid_glass,
					   install_inwindow_circle_glass, inwindow_glass_available, NATIVE_TITLEBAR_HEIGHT)
from watermelon_ui import (make_native_glass_window, make_glass_dialog, install_glass_dialog_class,
						   install_native_glass_window_class, watermelon_alert, watermelon_choice,
						   BusyCard, GREY_ROW_HEIGHT)
# Word / Excel / PowerPoint 文件（2026-11-20，样式书 5.11 / 5.14）：本地模式的文件下拉里和 Markdown 排在一起，
# 选中时编辑区整列换成打包进来的 Office 编辑组件（watermelon_office.py + office_editor_bridge.py + office_editor/）。
import watermelon_office
from watermelon_office import is_office_path, OfficePanel
import watermelon_attachments
import watermelon_broccoli
import broccoli_write_back     # 「Write Here with Broccoli…」（2026-11-25，和 Strawberry 共用同一份文件）
import watermelon_lecture
import watermelon_courseware
import watermelon_scan
import watermelon_anki
import watermelon_marks
import watermelon_outline
import watermelon_handles
import app_mcp_host
import watermelon_tools


def _read_local_text(path):
	"""本地模式一个文件的文字。Office 文件没有“文字”（由 Office 面板打开），返回空；文件不在了照常报错。"""
	if is_office_path(path):
		if not os.path.isfile(path):
			raise FileNotFoundError(path)
		return ''
	return codecs.open(path, 'r', encoding='utf-8').read()


# 界面语言（English / 简体中文 / 日本語）：在菜单栏图标的菜单里选，和数据放在一起，下次启动生效
# （和 Broccoli / Strawberry / Tomato 同一套；2026-11-20 Ryan：“中日文翻译当然是要做的”）。
UI_LANGUAGE = watermelon_ui.read_ui_language_setting(WATERMELON_DATA_DIR)
watermelon_ui.load_translation(UI_LANGUAGE, [os.path.join(BasePath, 'i18n'),
											 os.path.join(os.path.dirname(os.path.abspath(__file__)), 'i18n')])

NOTES_CACHE_PATH = os.path.join(SettingsPath, "notes_cache.json")
DEBUG_LAYOUT = False

MODE_BACKUP_LIMIT_MIN = 10
MODE_BACKUP_LIMIT_MAX = 20
DEFAULT_MODE_BACKUP_LIMIT = 20


def _watermelon_app_path():
	os.makedirs(WATERMELON_DATA_DIR, exist_ok=True)
	return WATERMELON_DATA_DIR


MODE_BACKUP_LIMIT_FILE = os.path.join(_watermelon_app_path(), "backup_limit.txt")


def _normalize_mode_backup_limit(value):
	try:
		limit = int(value)
	except Exception:
		return DEFAULT_MODE_BACKUP_LIMIT
	if limit < MODE_BACKUP_LIMIT_MIN:
		return MODE_BACKUP_LIMIT_MIN
	if limit > MODE_BACKUP_LIMIT_MAX:
		return MODE_BACKUP_LIMIT_MAX
	return limit


def save_mode_backup_limit(limit):
	normalized = _normalize_mode_backup_limit(limit)
	try:
		with open(MODE_BACKUP_LIMIT_FILE, 'w', encoding='utf-8') as f0:
			f0.write(str(normalized))
	except Exception:
		pass
	return normalized


def load_mode_backup_limit():
	try:
		if not os.path.exists(MODE_BACKUP_LIMIT_FILE):
			save_mode_backup_limit(DEFAULT_MODE_BACKUP_LIMIT)
			return DEFAULT_MODE_BACKUP_LIMIT
		raw = codecs.open(MODE_BACKUP_LIMIT_FILE, 'r', encoding='utf-8').read().strip()
		normalized = _normalize_mode_backup_limit(raw)
		if str(normalized) != raw:
			save_mode_backup_limit(normalized)
		return normalized
	except Exception:
		return DEFAULT_MODE_BACKUP_LIMIT


backup_limit_actions = {}


def _refresh_backup_limit_menu(selected=None):
	if selected is None:
		selected = load_mode_backup_limit()
	for value, action in backup_limit_actions.items():
		action.setChecked(value == selected)


def _set_backup_limit_from_menu(limit):
	selected = save_mode_backup_limit(limit)
	_refresh_backup_limit_menu(selected)
	target = globals().get("w3")
	if target is not None:
		try:
			target.apply_backup_limit_now(selected)
		except Exception:
			pass


# Create the icon
icon = QIcon(BasePath + "wtmenu.icns")

# Create the tray
# ── macOS 27：菜单栏图标点击闪退的规避（与 Broccoli 相同的修法）──
# macOS 27 的状态栏图标改由手势识别器驱动。Qt cocoa 插件（QCocoaSystemTrayIcon::emitActivated，
# 已发布的 Qt <= 6.11.2 都有）在菜单弹出时读取 NSApp.currentEvent —— 此时已是过期的 MouseExited
# 事件而不是那次点击 —— 并调用 -[NSEvent clickCount]。AppKit 对非鼠标事件会抛
# "Invalid message sent to event"，整个进程随之退出。Qt 只在开发分支修了（qt_mac_isMouseEvent 守卫），
# 在发布版 PyQt6-Qt6 带上修复之前，让非鼠标事件的 clickCount 返回 0 而不是抛异常；真正的鼠标事件照常走原实现。
_NSEVENT_CLICKCOUNT_GUARD = None


def _install_macos_nsevent_clickcount_guard():
	"""安装成功（或已安装）返回 True，否则 False。"""
	global _NSEVENT_CLICKCOUNT_GUARD
	if _NSEVENT_CLICKCOUNT_GUARD is not None:
		return True
	if sys.platform != 'darwin':
		return False
	try:
		import ctypes
		import ctypes.util
		ctypes.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
		lib = ctypes.CDLL(ctypes.util.find_library('objc') or '/usr/lib/libobjc.dylib')
		lib.objc_getClass.restype = ctypes.c_void_p
		lib.objc_getClass.argtypes = [ctypes.c_char_p]
		lib.sel_registerName.restype = ctypes.c_void_p
		lib.sel_registerName.argtypes = [ctypes.c_char_p]
		lib.class_getInstanceMethod.restype = ctypes.c_void_p
		lib.class_getInstanceMethod.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
		lib.method_getImplementation.restype = ctypes.c_void_p
		lib.method_getImplementation.argtypes = [ctypes.c_void_p]
		lib.method_setImplementation.restype = ctypes.c_void_p
		lib.method_setImplementation.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
		ns_event = lib.objc_getClass(b'NSEvent')
		sel_click = lib.sel_registerName(b'clickCount')
		sel_type = lib.sel_registerName(b'type')
		method = lib.class_getInstanceMethod(ns_event, sel_click) if ns_event else None
		if not method:
			return False
		imp_t = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)     # NSInteger (id, SEL)
		type_t = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)   # NSUInteger (id, SEL)
		original = imp_t(lib.method_getImplementation(method))
		event_type = type_t(ctypes.cast(lib.objc_msgSend, ctypes.c_void_p).value)
		# 允许 clickCount 的 NSEventType：左/右键按下与抬起、移动、左/右键拖动、其他键按下/抬起/拖动
		mouse_types = frozenset({1, 2, 3, 4, 5, 6, 7, 25, 26, 27})

		def _guarded_click_count(self_ptr, cmd_ptr):
			try:
				if self_ptr and event_type(self_ptr, sel_type) in mouse_types:
					return original(self_ptr, cmd_ptr)
			except Exception:
				pass
			return 0

		replacement = imp_t(_guarded_click_count)
		lib.method_setImplementation(method, ctypes.cast(replacement, ctypes.c_void_p).value)
		# 回调要活到进程结束（ObjC 运行时只持有裸指针）
		_NSEVENT_CLICKCOUNT_GUARD = (replacement, original, event_type, lib)
		return True
	except Exception:
		logging.exception('macOS NSEvent clickCount guard install failed')
		return False


_install_macos_nsevent_clickcount_guard()

tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()
action1 = QAction(_tr("🦾 Bold Text! (Clipboard)"))
menu.addAction(action1)

action4 = QAction(_tr("💪 Unbold Text! (Clipboard)"))
menu.addAction(action4)

menu.addSeparator()

action7 = QAction(_tr("📂️ Open a Markdown file"))
menu.addAction(action7)

menu.addSeparator()

action2 = QAction(_tr("✍️ Watermelon Typewriter"))
menu.addAction(action2)

# Dock 图标显示 / 隐藏、窗口在所有桌面显示（2026-11-20 Ryan：“隐藏 dock icon 和在所有 space 上显示的功能，
# 我需要你参照 tomato 和 strawberry 和 broccoli 去实现”——和那三个同一套写法、同样的菜单文字）。
# - Dock 图标：app 不带图标启动（Watermelon.spec 里 LSBackgroundOnly），运行时再显示，除非在这里关掉。关掉以后
#   Watermelon 只在菜单栏：没有 Dock 图标、没有程序菜单、不在 Command-Tab 里；窗口照旧从这个菜单和蓝条打开。
# - 所有桌面：每个窗口自己带“所有桌面 + 可以在别的 app 全屏旁边”的标记，每次显示时打（Qt 可能重建系统窗口）。
#   以前的“Assign to All Desktops”是用辅助功能去点 Dock 图标的菜单：图标一隐藏就点不到，还要权限，已删。
def _read_switch(name, default=True):
	try:
		return codecs.open(SettingsPath + name, 'r', encoding='utf-8').read().strip() != '0'
	except Exception:
		return default


def _write_switch(name, on):
	try:
		with open(SettingsPath + name, 'w', encoding='utf-8') as f0:
			f0.write('1' if on else '0')
	except Exception:
		logging.exception('Saving %s failed.', name)


def set_dock_icon_visible(visible, activate=False):
	"""（Broccoli 的。）有 Dock 图标的普通 app，或者没有图标的附属 app。"""
	try:
		from AppKit import NSApplication
		ns_app = NSApplication.sharedApplication()
		ns_app.setActivationPolicy_(0 if visible else 1)
		if visible and activate:
			ns_app.activateIgnoringOtherApps_(True)
		return True
	except Exception:
		logging.exception('Failed to change the Dock icon visibility.')
		return False


_NS_WINDOW_CAN_JOIN_ALL_SPACES = 1 << 0
_NS_WINDOW_MOVE_TO_ACTIVE_SPACE = 1 << 1
_NS_WINDOW_FULL_SCREEN_AUXILIARY = 1 << 8
SHOW_ON_ALL_SPACES = _read_switch('all_spaces.txt')
_ALL_SPACES_CLASSES = []


# Stage Manager (2026-11-25, Ryan about the sister app: "它有的时候左边显示就会突然空出来这么一块"; then "把修改同样给
# strawberry 和 raspberry" / "还有 watermelon"). The main window is a panel, not a document window: it is marked as
# one that belongs to no stage and shows with every app's (auxiliary + can join all applications, never
# primary), so the system has no stage to fit it into. On the real screen the mark alone was enough.
_NS_WINDOW_PRIMARY = 1 << 16
_NS_WINDOW_AUXILIARY = 1 << 17
_NS_WINDOW_CAN_JOIN_ALL_APPLICATIONS = 1 << 18


def keep_out_of_stage_manager(widget):
	if sys.platform != 'darwin' or QGuiApplication.platformName() != 'cocoa':
		return False   # no system window behind the widget (e.g. Qt drawing off screen)
	window = glass_kit._broccoli_own_ns_window(widget)
	if window is None:
		return False
	try:
		behavior = int(window.collectionBehavior())
		wanted = (behavior & ~_NS_WINDOW_PRIMARY) | _NS_WINDOW_AUXILIARY | _NS_WINDOW_CAN_JOIN_ALL_APPLICATIONS
		if wanted != behavior:
			window.setCollectionBehavior_(wanted)
			logging.info('Main window marked as outside Stage Manager: behaviour %#x -> %#x', behavior, int(window.collectionBehavior()))
		return True
	except Exception:
		logging.exception('Main window: the Stage Manager mark could not be set')
		return False


def show_window_on_all_spaces(widget, enabled=None):
	if sys.platform != 'darwin' or QGuiApplication.platformName() != 'cocoa':
		return False   # 窗口后面没有系统窗口（比如离屏绘制）
	window = glass_kit._broccoli_own_ns_window(widget)
	if window is None:
		return False
	enabled = SHOW_ON_ALL_SPACES if enabled is None else bool(enabled)
	bits = _NS_WINDOW_CAN_JOIN_ALL_SPACES | _NS_WINDOW_FULL_SCREEN_AUXILIARY
	try:
		behavior = int(window.collectionBehavior())
		wanted = behavior & ~_NS_WINDOW_MOVE_TO_ACTIVE_SPACE
		wanted = (wanted | bits) if enabled else (wanted & ~bits)
		if wanted != behavior:
			window.setCollectionBehavior_(wanted)
		return True
	except Exception:
		return False


def set_show_on_all_spaces(enabled):
	"""开关：现在开着的窗口和以后显示的每一个。"""
	global SHOW_ON_ALL_SPACES
	SHOW_ON_ALL_SPACES = bool(enabled)
	for widget in QApplication.topLevelWidgets():
		if isinstance(widget, tuple(_ALL_SPACES_CLASSES)) and widget.testAttribute(Qt.WidgetAttribute.WA_WState_Created):
			show_window_on_all_spaces(widget)


def install_all_spaces_class(cls):
	original = cls.showEvent

	def showEvent(self, event, _original=original):
		_original(self, event)
		show_window_on_all_spaces(self)

	cls.showEvent = showEvent
	_ALL_SPACES_CLASSES.append(cls)


def _toggle_dock_icon(checked):
	_write_switch('dock_icon.txt', bool(checked))
	set_dock_icon_visible(bool(checked), activate=bool(checked))


def _toggle_all_spaces(checked):
	_write_switch('all_spaces.txt', bool(checked))
	set_show_on_all_spaces(bool(checked))


action_dock_icon = QAction(_tr("👀 Show/Hide dock icon"))
action_dock_icon.setCheckable(True)
action_dock_icon.setChecked(_read_switch('dock_icon.txt'))
action_dock_icon.triggered.connect(_toggle_dock_icon)
menu.addAction(action_dock_icon)

action_all_spaces = QAction(_tr("🪟 Show on all Spaces"))
action_all_spaces.setCheckable(True)
action_all_spaces.setChecked(SHOW_ON_ALL_SPACES)
action_all_spaces.triggered.connect(_toggle_all_spaces)
menu.addAction(action_all_spaces)

action6 = QAction(_tr("⚙️ Settings"))
menu.addAction(action6)

backup_limit_menu = menu.addMenu(_tr("💾 Backup Limit"))
backup_limit_group = QActionGroup(menu)
backup_limit_group.setExclusive(True)
for value in range(MODE_BACKUP_LIMIT_MIN, MODE_BACKUP_LIMIT_MAX + 1):
	limit_action = QAction(str(value), menu)
	limit_action.setCheckable(True)
	limit_action.triggered.connect(lambda checked=False, v=value: _set_backup_limit_from_menu(v))
	backup_limit_group.addAction(limit_action)
	backup_limit_menu.addAction(limit_action)
	backup_limit_actions[value] = limit_action
_refresh_backup_limit_menu(load_mode_backup_limit())

teleprompter_action = QAction(_tr("📺 Teleprompter Mode"))
teleprompter_action.setCheckable(True)
menu.addAction(teleprompter_action)
open_backup_folder_action = QAction(_tr("🗂️ Open Current Backup Folder"))
menu.addAction(open_backup_folder_action)
lecture_action = QAction(_tr("🎓 Lecture Mode"))   # 听课模式的开关（Ryan 2026-11-21：“加在 menubar 里”）
lecture_action.setCheckable(True)
menu.addAction(lecture_action)
anki_action = QAction(_tr("🃏 Make Anki Cards…"))   # 从选中的文字（笔记 / 网页 / Office 文件）让 Broccoli 做 Anki 卡片
menu.addAction(anki_action)

# Watermelon's tools in any AI app that speaks MCP (2026-11-25): copies the lines such an app's MCP settings take.
action_ai_apps = QAction(_tr("🔌 Use in other AI apps…"))
menu.addAction(action_ai_apps)


def _copy_ai_apps_setup():
	QGuiApplication.clipboard().setText(app_mcp_host.bridge_setup_json())
	watermelon_alert(None, _tr('Use in other AI apps'),
					 _tr('The setup is copied. Paste it into the MCP settings of your AI app. '
						 'The AI app can then use the tools of Watermelon and of your other apps on this Mac.'))


action_ai_apps.triggered.connect(lambda _checked=False: _copy_ai_apps_setup())

# 界面语言：下次启动生效
lang_menu = QMenu(_tr("🌐 Language"))
menu.addMenu(lang_menu)
_lang_menu_actions = {}


def _on_ui_language_chosen(code):
	watermelon_ui.write_ui_language_setting(WATERMELON_DATA_DIR, code)
	for _code, _action in _lang_menu_actions.items():
		_action.setChecked(_code == code)
	if code != UI_LANGUAGE:
		watermelon_alert(None, _tr('Language'), _tr('The language setting will apply after Watermelon restarts.'))


for _lang_code, _lang_label in watermelon_ui.UI_LANGUAGES:
	_lang_action = QAction(_lang_label)
	_lang_action.setCheckable(True)
	_lang_action.setChecked(_lang_code == UI_LANGUAGE)
	_lang_action.triggered.connect(lambda _checked, c=_lang_code: _on_ui_language_chosen(c))
	_lang_menu_actions[_lang_code] = _lang_action
	lang_menu.addAction(_lang_action)

menu.addSeparator()

action5 = QAction(_tr("🆕 Check for Updates"))
menu.addAction(action5)

action3 = QAction(_tr("ℹ️ About"))
menu.addAction(action3)

menu.addSeparator()

# Add a Quit option to the menu.
quit = QAction(_tr("Quit"))
quit.triggered.connect(app.quit)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

# create a system menu
btna4 = QAction(_tr("&Watermelon Typewriter"))
btna4.setCheckable(True)
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu(_tr("&Actions"))
file_menu.addAction(btna4)


def is_dark_theme(app):
	if NSUserDefaults is None:
		return False
	defaults = NSUserDefaults.standardUserDefaults()
	style = defaults.stringForKey_("AppleInterfaceStyle")
	return style == "Dark"


def get_accent_color_hex():
	try:
		if NSColor is None:
			return "#0A84FF"
		accent = NSColor.controlAccentColor()
		rgb = accent.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
		if rgb:
			r = int(rgb.redComponent() * 255)
			g = int(rgb.greenComponent() * 255)
			b = int(rgb.blueComponent() * 255)
			return f"#{r:02X}{g:02X}{b:02X}"
	except Exception:
		pass
	return "#0A84FF"


def set_light_palette(app):
	palette = QPalette()
	palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
	palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
	palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
	palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
	palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
	palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
	app.setPalette(palette)


def set_dark_palette(app):
	palette = QPalette()
	palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
	palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
	palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
	palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
	palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
	palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
	app.setPalette(palette)


def _read_bg_pref():
	bg_pref_file = SettingsPath + 'bg_color.txt'
	try:
		if os.path.exists(bg_pref_file):
			pref = codecs.open(bg_pref_file, 'r', encoding='utf-8').read().strip()
			if pref in ('cream', 'white'):
				return pref
	except Exception:
		pass
	return 'white'


def _resolve_bg_color(pref, dark_mode):
	if pref == 'cream':
		return '#454540' if dark_mode else '#F3F2EE'
	return '#3A3A3A' if dark_mode else '#FFFFFF'


def _apply_window_palette(window, dark_mode):
	if window is None:
		return
	p = window.palette()
	p.setColor(window.backgroundRole(), QColor('#2D2D2D' if dark_mode else '#ECECEC'))
	window.setPalette(p)


def _apply_mac_button_theme():
	for widget in QApplication.allWidgets():
		if isinstance(widget, MacNormalButton):
			widget.update_theme()


# def _apply_dark_combo_style(combo):
# 	combo.setFixedHeight(22)
# 	combo.setStyleSheet("""
# 		QComboBox {
# 			border: 1px solid transparent;
# 			background-color: #404145;
# 			border-radius: 6px;
# 			padding: 1px 22px 1px 8px;
# 			color: #FFFFFF;
# 		}
# 		QComboBox:hover {
# 			background-color: #4A4B4F;
# 		}
		
# 		QComboBox QAbstractItemView {
# 			background-color: #404145;
# 			color: #FFFFFF;
# 			selection-background-color: #4A4B4F;
# 			border: 1px solid #2F3033;
# 			border-radius: 6px; 
# 		}
		
# 	""")


def apply_bg_color_from_pref(target=None):
	if target is None:
		target = globals().get("w3")
	if target is None:
		return
	pref = _read_bg_pref()
	bg_color = _resolve_bg_color(pref, is_dark_theme(app))
	target.set_bg_color(bg_color)


if NSObject is not None and objc is not None:
	class ThemeObserver(NSObject):
		def initWithApp_(self, app):
			self = objc.super(ThemeObserver, self).init()
			self.app = app
			return self

		def themeChanged_(self, notification):
			apply_theme(self.app)
else:
	class ThemeObserver:
		pass


def install_theme_observer(app):
	if NSDistributedNotificationCenter is None or NSSelectorFromString is None or NSObject is None or objc is None:
		return None
	try:
		observer = ThemeObserver.alloc().initWithApp_(app)
		center = NSDistributedNotificationCenter.defaultCenter()
		center.addObserver_selector_name_object_(
			observer,
			NSSelectorFromString("themeChanged:"),
			"AppleInterfaceThemeChangedNotification",
			None
		)
		return observer
	except Exception:
		return None


def apply_theme(app):
	dark_mode = is_dark_theme(app)
	if dark_mode:
		set_dark_palette(app)
		app.setStyleSheet(style_sheet_dark)
	else:
		set_light_palette(app)
		app.setStyleSheet(style_sheet_ori)
	target = globals().get("w3")
	if target is not None:
		_apply_window_palette(target, dark_mode)
		apply_bg_color_from_pref(target)
		try:
			target.set_textedit_font(target._current_font_size, target._current_font_family)
		except Exception:
			pass
	_apply_mac_button_theme()
	for widget in app.topLevelWidgets():
		widget.update()
	watermelon_ui.refresh_kit_theme(dark_mode)   # 白色胶囊、下拉、玻璃的深浅跟着换


# Initialize theme
if is_dark_theme(app):
	set_dark_palette(app)
else:
	set_light_palette(app)

theme_observer = install_theme_observer(app)


def is_newer_version(latest: str, current: str) -> bool:
	# 'v0.0.12' vs 'v0.0.11'
	def parse(v: str):
		return [int(x) for x in v.lstrip('vV').split('.')]
	try:
		return parse(latest) > parse(current)
	except Exception:
		return False


def play_sound_async(filepath):
	"""在后台线程中播放声音文件，播放完自动清除线程"""
	def _play():
		try:
			subprocess.call(['afplay', filepath])
		except Exception:
			pass
	t = threading.Thread(target=_play, daemon=True)
	t.start()


class GlassButton(QPushButton):
	"""打字机上的圆形按钮（样式书 5.1 圆形按钮）：系统液态玻璃圆片，直径 34（控件 38，四周各留 2），
	图标画进玻璃里；悬停 / 按下只加一层薄纱；开着的时候（setSelected）着系统强调色，和"图钉按下时着蓝"
	同一条规定。打字机是黑的，所以玻璃一直用深色。没有玻璃时（老系统、离屏、淡入淡出中）画同样大小的
	半透明圆片，界面不变形。"""

	def __init__(self, text="", radius=19, icon_path=None, momentary=True, parent=None, **_unused):
		super().__init__(text, parent)
		self.radius = radius
		self.momentary = momentary
		self.is_selected = False
		self.is_hovered = False
		self._icon_pixmap = None
		self._glass_foreground_pass = False
		self.setAutoDefault(False)
		if icon_path:
			self.setIconPath(icon_path)
		self.setStyleSheet("background-color: transparent; border: none; color: white; font-size: 16px; padding: 0px;")
		glass_button(
			self,
			tint_for=lambda b: b._selected_tint(),
			dark_for=lambda b: True,
			radius_for=lambda b: b._disc_rect().height() / 2.0,
			rect_for=lambda b: b._disc_rect(),
			# 淡入淡出时按钮上挂着透明度效果：系统玻璃不会跟着变淡，这段时间由 Qt 画同样的圆片
			wanted_for=lambda b: b.graphicsEffect() is None)

	def _disc_rect(self):
		return self.rect().adjusted(2, 2, -2, -2)

	def _selected_tint(self):
		if not self.is_selected:
			return None
		accent = QColor(get_accent_color_hex())
		accent.setAlpha(190)
		return accent

	def setIconPath(self, path):
		"""设置图标路径"""
		self._icon_pixmap = QPixmap(path) if path else None
		self.update()

	def setIconPixmap(self, pixmap):
		"""直接设置图标（用于代码绘制、没有图片文件的图标）"""
		self._icon_pixmap = pixmap
		self.update()

	def setRadius(self, radius):
		self.radius = radius
		self.update()

	def setSelected(self, selected: bool):
		self.is_selected = bool(selected)
		self.setProperty('wmSelected', self.is_selected)   # 属性变化 → 玻璃重新着色
		self.update()

	def enterEvent(self, event):
		self.is_hovered = True
		self.update()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.is_hovered = False
		self.update()
		super().leaveEvent(event)

	def hitButton(self, pos):
		path = QPainterPath()
		path.addEllipse(QRectF(self._disc_rect()))
		return path.contains(pos.toPointF() if hasattr(pos, 'toPointF') else pos)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
		rect = QRectF(self._disc_rect())
		glass = bool(getattr(self, '_liquid_glass_active', False)) or self._glass_foreground_pass
		if not glass:
			# 没有玻璃：同样大小的圆片（原来的半透明白 + 细白边）
			if not self.isEnabled():
				painter.setOpacity(0.35)
			if self.is_selected:
				fill = QColor(get_accent_color_hex())
				fill.setAlpha(190)
			elif self.isDown():
				fill = QColor(255, 255, 255, 56)
			elif self.is_hovered:
				fill = QColor(255, 255, 255, 38)
			else:
				fill = QColor(255, 255, 255, 20)
			painter.setBrush(QBrush(fill))
			painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
			painter.drawEllipse(rect.adjusted(0.5, 0.5, -0.5, -0.5))
		elif not self.isEnabled():
			painter.setOpacity(0.35)
		if self._icon_pixmap is not None and not self._icon_pixmap.isNull():
			icon_size = min(rect.width(), rect.height()) * 0.6
			ratio = max(1.0, float(self.devicePixelRatioF()))
			scaled = self._icon_pixmap.scaled(
				int(icon_size * ratio), int(icon_size * ratio),
				Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
			scaled.setDevicePixelRatio(ratio)
			width, height = scaled.width() / ratio, scaled.height() / ratio
			painter.drawPixmap(QRectF(rect.center().x() - width / 2.0, rect.center().y() - height / 2.0, width, height),
							   scaled, QRectF(scaled.rect()))
		elif self.text():
			painter.setPen(QPen(QColor(255, 255, 255, 255)))
			painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
		painter.end()


def _teleprompter_icon_pixmap():
	"""提词器图标：屏幕 + 两行字 + 支架。按 speaker.png 等现有图标的画法绘制
	（500×500 画布、白色约 85% 不透明、约 44px 圆头线条），资源包里不需要新图片。"""
	size = 500
	pixmap = QPixmap(size, size)
	pixmap.fill(Qt.GlobalColor.transparent)
	painter = QPainter(pixmap)
	painter.setRenderHint(QPainter.RenderHint.Antialiasing)
	pen = QPen(QColor(255, 255, 255, 216), 44)
	pen.setCapStyle(Qt.PenCapStyle.RoundCap)
	pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
	painter.setPen(pen)
	painter.setBrush(Qt.BrushStyle.NoBrush)
	painter.drawRoundedRect(QRectF(34, 52, 432, 300), 46, 46)  # 屏幕
	painter.drawLine(140, 162, 360, 162)  # 第一行字
	painter.drawLine(176, 244, 324, 244)  # 第二行字
	painter.drawLine(250, 352, 250, 440)  # 支架
	painter.drawLine(150, 448, 350, 448)  # 底座
	painter.end()
	return pixmap


# WhiteButton（白色胶囊 → 玻璃胶囊）、MacNormalButton（灰色普通按钮，永远不是玻璃）、DropdownButton
# （紧凑灰色下拉，弹出的是系统菜单）现在都用 glass_kit.py 里的，写法和原来一样。


class CustomMessageBox(QWidget):
	def __init__(
		self,
		text=None,
		parent=None,
		icon=None,
		buttons=(_tr("OK"),),
		default=0,
		fixed_size=(400, 200),
		show_close_button=True,
	):
		super().__init__(parent)
		# 样式书 5.7：对话框的窗口就是卡片 = 窗口玻璃、圆角 16、系统阴影；按钮是灰色普通按钮。
		# （提醒和询问已经改用系统提醒；这个类现在只是「备忘录选择」对话框的底子和万一用到的备用框。）
		make_glass_dialog(self)
		if fixed_size:
			self.setFixedSize(fixed_size[0], fixed_size[1])
		self.result = None
		self._dialog_result = None
		self._event_loop = None

		# 拖动支持
		self.drag_pos = None

		self.close_button = None   # 不再自己画红色圆点：Esc / 取消按钮关闭

		# 主内容
		self.body_layout = QVBoxLayout()
		self.body_layout.setContentsMargins(32, 40, 32, 32)
		self.body_layout.setSpacing(16)

		# 图标
		if icon:
			icon_label = QLabel()
			icon_label.setPixmap(icon.pixmap(48, 48))
			icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			self.body_layout.addWidget(icon_label)

		# 文本
		self.label = None
		if text is not None:
			label = QLabel(text)
			label.setWordWrap(True)
			label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
			label.setStyleSheet("font-size: 13px; background: transparent;")
			self.body_layout.addWidget(label, stretch=1)
			self.label = label

		# 按钮
		self.btns = []
		if buttons:
			btn_layout = QHBoxLayout()
			btn_layout.setSpacing(8)
			btn_layout.addStretch()
			for i, btn_text in enumerate(buttons):
				btn = MacNormalButton(btn_text)
				btn.setMinimumWidth(96)
				btn.clicked.connect(lambda checked, idx=i: self._on_btn(idx))
				btn_layout.addWidget(btn)
				self.btns.append(btn)
			self.body_layout.addLayout(btn_layout)

		self.setLayout(self.body_layout)
		if self.btns:
			default_idx = max(0, min(default, len(self.btns) - 1))
			self.btns[default_idx].setFocus()

	def _on_btn(self, idx):
		self.result = idx
		self.done(idx)

	def done(self, result):
		self.result = result
		self._dialog_result = result
		if self._event_loop is not None and self._event_loop.isRunning():
			self._event_loop.quit()
		self.close()

	def accept(self):
		self.done(1)

	def reject(self):
		self.done(-1)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.reject()
			return
		super().keyPressEvent(event)

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
			self.move(event.globalPosition().toPoint() - self.drag_pos)
			event.accept()

	def exec(self):
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.show()
		self._event_loop = QEventLoop()
		self._event_loop.exec()
		self._event_loop = None
		return self._dialog_result

	def closeEvent(self, event):
		if self._event_loop is not None and self._event_loop.isRunning():
			self._event_loop.quit()
		event.accept()


class WindowAbout(QWidget):  # 增加说明页面(About)
	def __init__(self):
		super().__init__()
		self.init_ui()

	def init_ui(self):
		# 样式书 5.7.2 / 5.10：系统红绿灯（新设计，固定大小所以黄绿灰掉）+ 窗口玻璃；400 × 600 同 Broccoli
		self.setUpMainWindow()
		make_native_glass_window(self)
		self.setFixedSize(400, 600)
		self.center()
		self.setWindowTitle(_tr('About'))
		self.setFocus()

	def setUpMainWindow(self):
		widg1 = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wtmenu.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumWidth(100)
		l1.setMaximumHeight(100)
		l1.setScaledContents(True)
		blay1 = QHBoxLayout()
		blay1.setContentsMargins(0, 0, 0, 0)
		blay1.addStretch()
		blay1.addWidget(l1)
		blay1.addStretch()
		widg1.setLayout(blay1)

		widg2 = QWidget()
		lbl0 = QLabel(NAME, self)
		font = QFont()
		font.setFamily("Arial")
		font.setBold(True)
		font.setPointSize(20)
		lbl0.setFont(font)
		blay2 = QHBoxLayout()
		blay2.setContentsMargins(0, 0, 0, 0)
		blay2.addStretch()
		blay2.addWidget(lbl0)
		blay2.addStretch()
		widg2.setLayout(blay2)

		widg3 = QWidget()
		lbl1 = QLabel(_tr('Version %n').replace('%n', VERSION), self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(lbl1)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		lbl2 = QLabel(_tr('Thanks for your love🤟.'), self)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		blay4.addStretch()
		blay4.addWidget(lbl2)
		blay4.addStretch()
		widg4.setLayout(blay4)

		widg5 = QWidget()
		lbl3 = QLabel(_tr('For more of my works, please visit the homepage🥰.'), self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.addStretch()
		blay5.addWidget(lbl3)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg6 = QWidget()
		lbl4 = QLabel(_tr('Special thanks to ut.code(); of the University of Tokyo❤️.'), self)
		blay6 = QHBoxLayout()
		blay6.setContentsMargins(0, 0, 0, 0)
		blay6.addStretch()
		blay6.addWidget(lbl4)
		blay6.addStretch()
		widg6.setLayout(blay6)

		widg7 = QWidget()
		lbl5 = QLabel(_tr('This app is under the protection of GPL-3.0 license.'), self)
		blay7 = QHBoxLayout()
		blay7.setContentsMargins(0, 0, 0, 0)
		blay7.addStretch()
		blay7.addWidget(lbl5)
		blay7.addStretch()
		widg7.setLayout(blay7)

		widg8 = QWidget()
		widg8.setFixedHeight(50)
		bt1 = WhiteButton(_tr('The Author'))
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.intro)
		bt2 = WhiteButton(_tr('Github Page'))
		bt2.setMinimumWidth(100)
		bt2.clicked.connect(self.homepage)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg8.setLayout(blay8)

		bt7 = WhiteButton(_tr('Buy me a cup of coffee☕'))
		bt7.setMinimumWidth(215)
		bt7.clicked.connect(self.coffee)
		widg8_5 = QWidget()
		widg8_5.setFixedHeight(50)
		blay8_5 = QHBoxLayout()
		blay8_5.setContentsMargins(0, 0, 0, 0)
		blay8_5.addStretch()
		blay8_5.addWidget(bt7)
		blay8_5.addStretch()
		widg8_5.setLayout(blay8_5)

		widg9 = QWidget()
		widg9.setFixedHeight(70)
		bt3 = WhiteButton('🍪\n¥5')
		bt3.setMaximumHeight(50)
		bt3.setMinimumHeight(50)
		bt3.setMinimumWidth(50)
		bt3.clicked.connect(self.donate)
		bt4 = WhiteButton('🥪\n¥10')
		bt4.setMaximumHeight(50)
		bt4.setMinimumHeight(50)
		bt4.setMinimumWidth(50)
		bt4.clicked.connect(self.donate2)
		bt5 = WhiteButton('🍜\n¥20')
		bt5.setMaximumHeight(50)
		bt5.setMinimumHeight(50)
		bt5.setMinimumWidth(50)
		bt5.clicked.connect(self.donate3)
		bt6 = WhiteButton('🍕\n¥50')
		bt6.setMaximumHeight(50)
		bt6.setMinimumHeight(50)
		bt6.setMinimumWidth(50)
		bt6.clicked.connect(self.donate4)
		blay9 = QHBoxLayout()
		blay9.setContentsMargins(0, 0, 0, 0)
		blay9.addStretch()
		blay9.addWidget(bt3)
		blay9.addWidget(bt4)
		blay9.addWidget(bt5)
		blay9.addWidget(bt6)
		blay9.addStretch()
		widg9.setLayout(blay9)

		widg10 = QWidget()
		lbl6 = QLabel('© 2022 Yixiang SHEN. All rights reserved.', self)
		blay10 = QHBoxLayout()
		blay10.setContentsMargins(0, 0, 0, 0)
		blay10.addStretch()
		blay10.addWidget(lbl6)
		blay10.addStretch()
		widg10.setLayout(blay10)

		main_h_box = QVBoxLayout()
		main_h_box.setContentsMargins(20, 40, 20, 20)  # 重要，用来保证关闭按钮的位置。
		main_h_box.addSpacing(10)
		main_h_box.addWidget(widg1)
		main_h_box.addWidget(widg2)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg3)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg4)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg5)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg6)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg7)
		main_h_box.addStretch()
		main_h_box.addWidget(widg8)
		main_h_box.addWidget(widg8_5)
		main_h_box.addWidget(widg9)
		main_h_box.addWidget(widg10)
		main_h_box.addStretch()
		main_h_box.addSpacing(10)
		self.setLayout(main_h_box)

	def intro(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Ryan-the-hito')

	def homepage(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Watermelon')

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def donate(self):
		dlg = CustomDialog()
		dlg.exec()

	def donate2(self):
		dlg = CustomDialog2()
		dlg.exec()

	def donate3(self):
		dlg = CustomDialog3()
		dlg.exec()

	def donate4(self):
		dlg = CustomDialog4()
		dlg.exec()

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()


class CustomDialog(QDialog):  # (About1)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)   # 红绿灯 + 窗口玻璃（样式书 5.7.2）
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Or buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(200)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog2(QDialog):  # (About2)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)   # 红绿灯 + 窗口玻璃（样式书 5.7.2）
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Or buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(200)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog3(QDialog):  # (About3)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)   # 红绿灯 + 窗口玻璃（样式书 5.7.2）
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Or buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(200)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


class CustomDialog4(QDialog):  # (About4)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setUpMainWindow()
		make_native_glass_window(self, kind=Qt.WindowType.Dialog)   # 红绿灯 + 窗口玻璃（样式书 5.7.2）
		self.setWindowTitle(_tr("Thank you for your support!"))
		self.setFixedSize(400, 420)
		self.center()
		self.setFocus()

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = QPixmap(BasePath + 'wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = QPixmap(BasePath + 'alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel(_tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(_tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(_tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(_tr('Or buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(200)
		bt2.clicked.connect(self.coffee)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg_c.setLayout(blay8)

		self.layout = QVBoxLayout()
		self.layout.addWidget(widge_all)
		self.layout.addWidget(m1)
		self.layout.addWidget(m2)
		self.layout.addStretch()
		self.layout.addWidget(widg_c)
		self.layout.addStretch()
		self.setLayout(self.layout)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def coffee(self):
		webbrowser.open('https://www.buymeacoffee.com/ryanthehito')

	def cancel(self):  # 设置取消键的功能
		self.close()


# ---- 一键更新：下载 → 校验 → 安装 → 重启（照 Broccoli 2026-10-06 的做法移植）---------
# 每个版本在 GitHub 发布一个公证过的 DMG（接口里该文件的 digest 就是它的 sha256）。
#  1. 更新窗口把 DMG 下载到 ~/Library/Caches/com.ryanthehito.watermelon/Updates，显示进度条（先写 .part，
#     断了下次用 HTTP Range 续传），下完核对大小和 sha256。
#  2. 只读挂载 DMG（DMG 会先弹许可协议，所以往标准输入回答 "Y"），把 Watermelon.app 复制到
#     正在运行的 app 旁边的隐藏文件夹（同一个磁盘，之后的替换只是改名），并要求复制品满足
#     WATERMELON_UPDATE_CODE_REQUIREMENT（Developer ID + 本团队 + 本 bundle id）：
#     被改过的、别人签名的安装包一律不装。
#  3. Watermelon 正常退出；app.exec() 返回之后，由这个进程自己完成替换。macOS 的“App 管理”
#     允许 app 修改同一团队签名的 app；在本进程里换，归属最确定（退出后才跑的辅助脚本不一定算数）。
#  4. 一个脱离出去的小进程等本进程退出后重新打开 app。新版本第一次启动时删掉旧版本，并报告结果。
# 同一个 Developer ID 签名也让 macOS 的隐私权限（辅助功能等）在替换后继续有效。
WATERMELON_UPDATE_LATEST_API = 'https://api.github.com/repos/Ryan-the-hito/Watermelon/releases/latest'
WATERMELON_UPDATE_RELEASES_URL = 'https://github.com/Ryan-the-hito/Watermelon/releases'
WATERMELON_UPDATE_BUNDLE_ID = WATERMELON_BUNDLE_ID
WATERMELON_UPDATE_TEAM_ID = '49C7YMHM5Q'
WATERMELON_UPDATE_CODE_REQUIREMENT = (
	'anchor apple generic and identifier "%s"'
	' and certificate 1[field.1.2.840.113635.100.6.2.6] exists'      # Developer ID CA
	' and certificate leaf[field.1.2.840.113635.100.6.1.13] exists'  # Developer ID Application
	' and certificate leaf[subject.OU] = "%s"' % (WATERMELON_UPDATE_BUNDLE_ID, WATERMELON_UPDATE_TEAM_ID))
WATERMELON_UPDATE_CACHE_DIR = os.path.join(WATERMELON_CACHE_ROOT, 'Updates')
WATERMELON_UPDATE_RESULT_PATH = os.path.join(WATERMELON_UPDATE_CACHE_DIR, 'last_install.json')
WATERMELON_UPDATE_STAGING_DIRNAME = '.Watermelon-update'
_WATERMELON_UPDATE_FS_LOCK = threading.Lock()   # 准备新版本 vs. 启动时清理同一个文件夹
_WATERMELON_PENDING_UPDATE_INSTALL = None        # 为安装而退出前才设置
# 设置文件现在在 Application Support 里（WATERMELON_SETTINGS_DIR），更新换掉整个 app 也不受影响。


class WatermelonUpdateError(Exception):
	"""可以直接显示给用户的更新失败原因。"""


class WatermelonUpdateCanceled(WatermelonUpdateError):
	pass


def watermelon_running_app_bundle():
	"""本进程所在的 .app（只有打包版有）。"""
	if not getattr(sys, 'frozen', False):
		return None
	try:
		bundle = Path(sys.executable).resolve().parents[2]
	except Exception:
		return None
	if bundle.suffix != '.app' or not (bundle / 'Contents' / 'Info.plist').is_file():
		return None
	return bundle


def watermelon_update_install_blocker(bundle):
	"""这份 Watermelon 为什么不能替换自己（能替换时返回空字符串）。"""
	if sys.platform != 'darwin':
		return _tr('automatic install needs macOS')
	if bundle is None:
		return _tr('Watermelon is not running from an installed app')
	if '/AppTranslocation/' in str(bundle):
		return _tr('macOS is running Watermelon from a temporary copy; move it into Applications first')
	# 把 app 改名挪走，需要它和它所在文件夹的写权限
	if not os.access(str(bundle.parent), os.W_OK) or not os.access(str(bundle), os.W_OK):
		return _tr('no permission to replace %1').replace('%1', str(bundle))
	return ''


def watermelon_fetch_latest_release():
	"""从 GitHub 接口取最新版本：版本号和它的 DMG（没有 DMG 时 dmg_* 留空）。"""
	response = requests.get(WATERMELON_UPDATE_LATEST_API, timeout=(4, 6),
							headers={'Accept': 'application/vnd.github+json'})
	if not response.ok:
		return None
	data = response.json() or {}
	tag = str(data.get('tag_name', '') or '').strip()
	if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
		return None
	info = {'tag': tag, 'version': tag[1:], 'dmg_name': '', 'dmg_url': '', 'dmg_size': 0, 'dmg_sha256': ''}
	dmgs = [asset for asset in (data.get('assets') or []) if isinstance(asset, dict)
			and str(asset.get('name', '')).lower().endswith('.dmg')
			and str(asset.get('state', 'uploaded')) == 'uploaded'
			and str(asset.get('browser_download_url', '')).startswith('https://')]
	dmgs.sort(key=lambda asset: not str(asset.get('name', '')).lower().startswith('watermelon'))
	if dmgs:
		asset = dmgs[0]
		digest = str(asset.get('digest') or '')
		info.update(dmg_name=str(asset.get('name')),
					dmg_url=str(asset.get('browser_download_url')),
					dmg_size=int(asset.get('size') or 0),
					dmg_sha256=digest[7:].lower() if digest.lower().startswith('sha256:') else '')
	return info


def _watermelon_sha256_file(path):
	digest = hashlib.sha256()
	with open(path, 'rb') as handle:
		for block in iter(lambda: handle.read(4 << 20), b''):
			digest.update(block)
	return digest.hexdigest()


def _watermelon_update_file_matches(path, size, sha256):
	try:
		if size and os.path.getsize(path) != size:
			return False
		return not sha256 or _watermelon_sha256_file(path) == sha256
	except OSError:
		return False


def watermelon_download_update_dmg(info, progress, cancel_event, status=None):
	"""把这个版本的 DMG 下载到缓存（接着上次的 .part 续传），核对大小和 sha256 后返回路径。
	progress(done, total) 和 status(text) 在调用它的后台线程里执行；cancel_event 在两块数据之间
	中止下载，.part 留着下次续传。"""
	status = status or (lambda _text: None)
	url = str(info.get('dmg_url') or '')
	if not url:
		raise WatermelonUpdateError(_tr('This release has no installer package.'))
	size = int(info.get('dmg_size') or 0)
	sha256 = str(info.get('dmg_sha256') or '').lower()
	os.makedirs(WATERMELON_UPDATE_CACHE_DIR, exist_ok=True)
	name = re.sub(r'[^A-Za-z0-9._-]+', '_', str(info.get('dmg_name') or '')).strip('.') or 'Watermelon-update.dmg'
	final_path = os.path.join(WATERMELON_UPDATE_CACHE_DIR, name)
	part_path = final_path + '.part'
	if os.path.isfile(final_path):
		status(_tr('Verifying the download…'))
		if _watermelon_update_file_matches(final_path, size, sha256):
			return final_path
		os.remove(final_path)
	have = os.path.getsize(part_path) if os.path.isfile(part_path) else 0
	if size and have > size:
		os.remove(part_path)
		have = 0
	if not size or have < size:
		headers = {'Range': 'bytes=%d-' % have} if have else {}
		try:
			with requests.get(url, stream=True, timeout=(10, 60), headers=headers) as response:
				if have and response.status_code == 206:
					mode = 'ab'
				elif response.status_code == 200:
					mode, have = 'wb', 0
				else:
					raise WatermelonUpdateError(_tr('Download failed (HTTP %1).').replace('%1', str(response.status_code)))
				total = size or (have + int(response.headers.get('Content-Length') or 0))
				progress(have, total)
				with open(part_path, mode) as handle:
					for chunk in response.iter_content(chunk_size=1 << 20):
						if cancel_event.is_set():
							raise WatermelonUpdateCanceled(_tr('Download canceled.'))
						if chunk:
							handle.write(chunk)
							have += len(chunk)
							progress(have, total)
		except WatermelonUpdateError:
			raise
		except Exception as exc:
			if cancel_event.is_set():   # 点了取消时连接正好卡住：等到读超时才回来，也算取消
				raise WatermelonUpdateCanceled(_tr('Download canceled.')) from exc
			raise WatermelonUpdateError(_tr('Download interrupted: %1').replace('%1', str(exc))) from exc
	status(_tr('Verifying the download…'))
	if not _watermelon_update_file_matches(part_path, size, sha256):
		try:
			os.remove(part_path)
		except OSError:
			pass
		raise WatermelonUpdateError(_tr('The download is damaged (checksum mismatch). Please try again.'))
	os.replace(part_path, final_path)
	return final_path


def _watermelon_attach_dmg(dmg_path, mountpoint):
	env = dict(os.environ, PAGER='/bin/cat')
	commands = (
		['/usr/bin/hdiutil', 'attach', '-nobrowse', '-readonly', '-noautoopen', '-noverify',
		 '-mountpoint', mountpoint, dmg_path],
		# macOS 27 起 hdiutil 被标为过时，diskutil image 是它的接班人
		['/usr/sbin/diskutil', 'image', 'attach', '--mountOptions', 'nobrowse', '--readOnly',
		 '--mountPoint', mountpoint, dmg_path],
	)
	for command in commands:
		if not os.path.exists(command[0]):
			continue
		try:
			# 发布的 DMG 挂载前会先显示许可协议，回答 "Y" 表示同意
			subprocess.run(command, input=b'Y\n', capture_output=True, timeout=300, env=env)
		except Exception:
			continue
		if os.path.ismount(mountpoint):
			return
	raise WatermelonUpdateError(_tr('Could not open the downloaded installer.'))


def _watermelon_detach_dmg(mountpoint):
	for command in (['/usr/bin/hdiutil', 'detach', mountpoint, '-quiet'],
					['/usr/bin/hdiutil', 'detach', mountpoint, '-force', '-quiet'],
					['/usr/sbin/diskutil', 'eject', mountpoint]):
		if not os.path.ismount(mountpoint):
			break
		if not os.path.exists(command[0]):
			continue
		try:
			subprocess.run(command, capture_output=True, timeout=60)
		except Exception:
			pass
	if not os.path.ismount(mountpoint):
		try:
			os.rmdir(mountpoint)
		except OSError:
			pass


def _watermelon_bundle_info(bundle):
	try:
		with open(Path(bundle) / 'Contents' / 'Info.plist', 'rb') as handle:
			data = plistlib.load(handle)
		return data if isinstance(data, dict) else {}
	except Exception:
		return {}


def watermelon_verify_update_bundle(bundle):
	"""整个签名满足 WATERMELON_UPDATE_CODE_REQUIREMENT 时返回它的版本号，否则抛 WatermelonUpdateError。"""
	info = _watermelon_bundle_info(bundle)
	if info.get('CFBundleIdentifier') != WATERMELON_UPDATE_BUNDLE_ID:
		raise WatermelonUpdateError(_tr('The installer does not contain Watermelon.'))
	try:
		result = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict',
								 '-R=' + WATERMELON_UPDATE_CODE_REQUIREMENT, str(bundle)],
								capture_output=True, timeout=900)
	except Exception as exc:
		raise WatermelonUpdateError(_tr('Could not check the signature: %1').replace('%1', str(exc))) from exc
	if result.returncode != 0:
		logging.warning('Update bundle rejected by codesign: %s',
						result.stderr.decode('utf-8', 'replace')[-800:])
		raise WatermelonUpdateError(_tr('The update is not signed by the Watermelon developer, so it was not installed.'))
	return str(info.get('CFBundleShortVersionString') or '')


def watermelon_stage_update(dmg_path, target, status=None):
	"""把 DMG 里的 Watermelon.app 复制到 <target 所在文件夹>/.Watermelon-update 并核验复制品。
	返回事件循环结束后要执行的安装记录（watermelon_apply_pending_update_install）。"""
	status = status or (lambda _text: None)
	target = Path(target)
	staging_root = target.parent / WATERMELON_UPDATE_STAGING_DIRNAME
	staged = staging_root / target.name
	with _WATERMELON_UPDATE_FS_LOCK:
		try:
			if staging_root.exists():
				shutil.rmtree(staging_root, ignore_errors=True)
			staging_root.mkdir(parents=True, exist_ok=True)
			os.makedirs(WATERMELON_UPDATE_CACHE_DIR, exist_ok=True)
			mountpoint = tempfile.mkdtemp(prefix='mnt-', dir=WATERMELON_UPDATE_CACHE_DIR)
			try:
				status(_tr('Opening the installer…'))
				_watermelon_attach_dmg(dmg_path, mountpoint)
				source = next((entry for entry in sorted(Path(mountpoint).iterdir())
							   if entry.suffix == '.app' and entry.is_dir() and not entry.is_symlink()
							   and _watermelon_bundle_info(entry).get('CFBundleIdentifier') == WATERMELON_UPDATE_BUNDLE_ID),
							  None)
				if source is None:
					raise WatermelonUpdateError(_tr('The installer does not contain Watermelon.'))
				status(_tr('Copying the new version…'))
				copied = subprocess.run(['/usr/bin/ditto', str(source), str(staged)],
										capture_output=True, timeout=1800)
				if copied.returncode != 0 or not staged.is_dir():
					raise WatermelonUpdateError(_tr('Could not copy the new version: %1').replace(
						'%1', copied.stderr.decode('utf-8', 'replace').strip()[-300:]))
			finally:
				_watermelon_detach_dmg(mountpoint)
			subprocess.run(['/usr/bin/xattr', '-dr', 'com.apple.quarantine', str(staged)],
						   capture_output=True, timeout=300)
			status(_tr('Checking the developer signature…'))
			version = watermelon_verify_update_bundle(staged)
			if is_newer_version(VERSION, version):
				raise WatermelonUpdateError(_tr('The installer holds an older version (v%1); nothing was changed.').replace('%1', str(version)))
		except Exception as exc:
			shutil.rmtree(staging_root, ignore_errors=True)
			if isinstance(exc, WatermelonUpdateError):
				raise
			raise WatermelonUpdateError(_tr('Could not prepare the update: %1').replace('%1', str(exc))) from exc
	return {'target': str(target), 'staged': str(staged),
			'backup': str(staging_root / ('previous-' + target.name)),
			'version': version, 'dmg': str(dmg_path)}


def _watermelon_write_update_result(record):
	try:
		os.makedirs(WATERMELON_UPDATE_CACHE_DIR, exist_ok=True)
		with open(WATERMELON_UPDATE_RESULT_PATH, 'w', encoding='utf-8') as handle:
			json.dump(record, handle, ensure_ascii=False)
	except Exception:
		pass


def watermelon_take_last_update_result():
	"""上一次运行安装更新后留下的记录（只读一次）。"""
	try:
		with open(WATERMELON_UPDATE_RESULT_PATH, 'r', encoding='utf-8') as handle:
			record = json.load(handle)
	except Exception:
		return {}
	try:
		os.remove(WATERMELON_UPDATE_RESULT_PATH)
	except OSError:
		pass
	return record if isinstance(record, dict) else {}


def _watermelon_spawn_relauncher(app_path):
	"""本进程退出后重新打开 app_path（卡住约 60 秒就强制结束）。两次 fork：等待的小进程挂到
	launchd 下面，退出时清理子进程也碰不到它。"""
	waiter = ('pid=$1; app=$2; n=0; '
			  'while kill -0 "$pid" 2>/dev/null; do '
			  'n=$((n+1)); if [ "$n" -ge 300 ]; then kill -9 "$pid" 2>/dev/null; sleep 1; break; fi; '
			  'sleep 0.2; done; sleep 0.5; /usr/bin/open "$app"')
	try:
		subprocess.Popen(['/bin/sh', '-c', '(' + waiter + ') </dev/null >/dev/null 2>&1 &',
						  'watermelon-relaunch', str(os.getpid()), str(app_path)],
						 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
						 start_new_session=True, close_fds=True).wait(timeout=10)
	except Exception:
		pass


def watermelon_apply_pending_update_install():
	"""app.exec() 返回后执行：换上准备好的新版本，记下结果，安排重新打开。
	改名失败就换回旧版本并重新打开它，旧版本启动后会说明原因（更新窗口的启动提示）。"""
	pending = _WATERMELON_PENDING_UPDATE_INSTALL
	if not pending:
		return
	target, staged, backup = Path(pending['target']), Path(pending['staged']), Path(pending['backup'])
	record = {'status': 'failed', 'version': str(pending.get('version') or ''), 'previous': VERSION,
			  'dmg': str(pending.get('dmg') or ''), 'reason': '', 'time': time.time()}
	try:
		# 退出钩子趁旧版本的文件都还在原处时先跑
		atexit._run_exitfuncs()
	except Exception:
		pass
	launch = target
	try:
		if not staged.is_dir():
			raise FileNotFoundError(str(staged))
		if backup.exists():
			shutil.rmtree(backup, ignore_errors=True)
		os.rename(target, backup)
		try:
			os.rename(staged, target)
		except OSError:
			try:
				os.rename(backup, target)
			except OSError:
				launch = backup
			raise
		record['status'] = 'installed'
	except Exception as exc:
		record['reason'] = '%s: %s' % (type(exc).__name__, exc)
	_watermelon_write_update_result(record)
	_watermelon_spawn_relauncher(str(launch))


def watermelon_cleanup_update_leftovers():
	"""启动时（后台线程）：删掉上次替换留下的旧版本或没用上的复制品、残留的挂载点，
	以及本版本已经达到的旧安装包。安装失败的 DMG 留着重试。"""
	with _WATERMELON_UPDATE_FS_LOCK:
		bundle = watermelon_running_app_bundle()
		if bundle is not None:
			staging_root = bundle.parent / WATERMELON_UPDATE_STAGING_DIRNAME
			if staging_root.is_dir():
				shutil.rmtree(staging_root, ignore_errors=True)
		if not os.path.isdir(WATERMELON_UPDATE_CACHE_DIR):
			return
		for name in os.listdir(WATERMELON_UPDATE_CACHE_DIR):
			path = os.path.join(WATERMELON_UPDATE_CACHE_DIR, name)
			try:
				if name.startswith('mnt-') and os.path.isdir(path):
					_watermelon_detach_dmg(path)
				elif name.endswith(('.dmg', '.dmg.part')):
					found = re.search(r'(\d+)\.(\d+)\.(\d+)', name)
					if not found or not is_newer_version('.'.join(found.groups()), VERSION):
						os.remove(path)
			except Exception:
				pass


class _UpdateProgressBar(QWidget):
	"""更新窗口里的细长圆角进度条。busy=True 时来回扫一段（挂载 / 复制 / 查签名没有百分比）。"""

	def __init__(self, parent=None):
		super().__init__(parent)
		self._fraction = 0.0
		self._busy = False
		self._phase = 0.0
		self._timer = QTimer(self)
		self._timer.setInterval(30)
		self._timer.timeout.connect(self._advance)
		self.setFixedHeight(6)

	def set_fraction(self, fraction):
		self._busy = False
		self._timer.stop()
		self._fraction = max(0.0, min(1.0, float(fraction)))
		self.update()

	def set_busy(self, busy=True):
		self._busy = bool(busy)
		if self._busy and self.isVisible():
			self._timer.start()
		else:
			self._timer.stop()
		self.update()

	def showEvent(self, event):
		super().showEvent(event)
		if self._busy:
			self._timer.start()

	def hideEvent(self, event):
		self._timer.stop()
		super().hideEvent(event)

	def _advance(self):
		self._phase = (self._phase + 0.015) % 1.0
		self.update()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		rect = QRectF(self.rect())
		radius = rect.height() / 2.0
		dark = is_dark_theme(app)
		track = QPainterPath()
		track.addRoundedRect(rect, radius, radius)
		painter.fillPath(track, QColor('#3A3A3C') if dark else QColor('#E5E5EA'))
		if self._busy:
			segment = rect.width() * 0.3
			fill_rect = QRectF(rect.left() - segment + (rect.width() + segment) * self._phase,
							   rect.top(), segment, rect.height())
		else:
			fill_rect = QRectF(rect.left(), rect.top(), rect.width() * self._fraction, rect.height())
		if fill_rect.width() > 0:
			fill = QPainterPath()
			fill.addRoundedRect(fill_rect, radius, radius)
			painter.setClipPath(track)
			painter.fillPath(fill, QColor('#0A84FF') if dark else QColor('#007AFF'))


class _UpdateStatusLabel(QLabel):
	"""更新窗口的状态行；字一变就告诉窗口（窗口只在它有话说时显示它，并按它调整高度）。同 Broccoli。"""
	text_changed = None

	def setText(self, text):
		super().setText(text)
		if callable(self.text_changed):
			self.text_changed()


class WindowUpdate(QWidget):  # 增加更新页面（Check for Updates）
	# 后台查询线程 → 界面线程：(显示文字, 有新版本, 有新版本时弹出窗口, 版本信息)
	update_check_finished = pyqtSignal(str, bool, bool, object)
	# 一键安装的后台线程 → 界面线程
	install_progress = pyqtSignal(object, object)   # (已下载字节, 总字节)
	install_status = pyqtSignal(str)                # 没有百分比的阶段
	install_failed = pyqtSignal(str)
	install_ready = pyqtSignal(object)              # 待安装记录

	def __init__(self):
		super().__init__()
		self._check_inflight = False
		self._release_info = None
		self._update_available = False
		self._install_busy = False
		self._install_can_cancel = False
		self._install_cancel = None
		self._download_started_at = 0.0
		self._download_started_bytes = 0
		self._startup_note = self._read_startup_note()
		self.update_check_finished.connect(self._on_update_check_finished)
		self.install_progress.connect(self._on_install_progress)
		self.install_status.connect(self._on_install_status)
		self.install_failed.connect(self._on_install_failed)
		self.install_ready.connect(self._on_install_ready)

		self.init_ui()

	def init_ui(self):
		# 样式书 5.7.2 / 5.10：系统红绿灯 + 窗口玻璃；宽 320、高随内容。排版照搬 Broccoli 现在的更新窗口（2026-11-25，
		# Ryan：“所有的软件……都是要学习 Broccoli 的这个更新写法的”）：和 About 一样居中，先写当前版本、再写最新版本，
		# 两行按钮共用一列文字、一列按钮；进度条和状态行只在有话说时出现，窗口跟着长高（上边不动）。
		self.setUpMainWindow()
		make_native_glass_window(self)
		QWidget.layout(self).setContentsMargins(20, NATIVE_TITLEBAR_HEIGHT, 20, 20)
		self.setFixedWidth(320)
		self._fit_height()
		self.center()
		self.setWindowTitle(_tr('Watermelon Updates'))
		self.setFocus()

	def _fit_height(self):
		"""和内容一样高，底下不留空；下载时进度条和状态行出现在按钮下面，窗口长出这么多（上面的东西不动）。"""
		layout = self.layout()
		if layout is None:
			return
		busy = not self.install_progress_bar.isHidden() or bool(self.install_status_lbl.text().strip())
		self._progress_block.setVisible(busy)
		layout.activate()
		width = self.width() or 320
		height = layout.totalHeightForWidth(width) if layout.hasHeightForWidth() else layout.totalSizeHint().height()
		self.setFixedHeight(max(1, int(height)))

	def setUpMainWindow(self):
		title = QLabel(_tr("<h2>Watermelon Update</h2>"), self)
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.lbl = QLabel(_tr('Current version: v%n').replace('%n', VERSION), self)
		self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

		widg5 = QWidget()
		lbl1 = QLabel(_tr('Latest version:'), self)
		self.lbl2 = QLabel('', self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.setSpacing(4)
		blay5.addStretch(1)
		blay5.addWidget(lbl1)
		blay5.addWidget(self.lbl2)
		blay5.addStretch(1)
		widg5.setLayout(blay5)

		lbl0 = QLabel(_tr('Check release:'), self)
		bt1 = WhiteButton('Github')
		bt1.setFixedWidth(120)
		bt1.clicked.connect(self.upd)
		# 一键更新：下载（带进度）→ 校验 → 安装 → 重启
		lbl_install = QLabel(_tr('Install update:'), self)
		self.install_btn = WhiteButton(_tr('Update Now'))
		self.install_btn.setFixedWidth(120)
		self.install_btn.setEnabled(False)
		self.install_btn.clicked.connect(self.start_install)
		label_width = max(lbl0.sizeHint().width(), lbl_install.sizeHint().width())
		action_rows = []
		for label, button in ((lbl0, bt1), (lbl_install, self.install_btn)):
			label.setFixedWidth(label_width)
			label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
			row = QWidget()
			row.setFixedHeight(50)   # About 的按钮行
			row_layout = QHBoxLayout(row)
			row_layout.setContentsMargins(0, 0, 0, 0)
			row_layout.setSpacing(12)
			row_layout.addStretch(1)
			row_layout.addWidget(label)
			row_layout.addWidget(button)
			row_layout.addStretch(1)
			action_rows.append(row)

		# 进度条 + 状态行：只在有东西可显示时出现
		self._progress_block = QWidget()
		progress_layout = QVBoxLayout(self._progress_block)
		progress_layout.setContentsMargins(0, 6, 0, 0)
		progress_layout.setSpacing(10)
		self.install_progress_bar = _UpdateProgressBar(self._progress_block)
		self.install_progress_bar.hide()
		self.install_status_lbl = _UpdateStatusLabel(self._progress_block)
		self.install_status_lbl.setWordWrap(True)
		self.install_status_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.install_status_lbl.text_changed = lambda: QTimer.singleShot(0, self._fit_height)
		progress_layout.addWidget(self.install_progress_bar)
		progress_layout.addWidget(self.install_status_lbl)
		self.install_progress_bar.installEventFilter(self)
		self._progress_block.hide()

		main_h_box = QVBoxLayout()
		main_h_box.setContentsMargins(20, 40, 20, 20)
		main_h_box.addSpacing(10)
		main_h_box.addWidget(title)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(self.lbl)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg5)
		main_h_box.addSpacing(16)
		for row in action_rows:
			main_h_box.addWidget(row)
		main_h_box.addWidget(self._progress_block)
		main_h_box.addSpacing(10)
		self.setLayout(main_h_box)

	def eventFilter(self, obj, event):
		if obj is getattr(self, 'install_progress_bar', None) and event.type() in (QEvent.Type.Show, QEvent.Type.Hide):
			QTimer.singleShot(0, self._fit_height)
		return super().eventFilter(obj, event)

	def upd(self):
		webbrowser.open(WATERMELON_UPDATE_RELEASES_URL)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()
		self.checkupdate()

	@staticmethod
	def _read_startup_note():
		record = watermelon_take_last_update_result()
		if record.get('status') == 'installed' and not is_newer_version(str(record.get('version') or ''), VERSION):
			return _tr('Watermelon was updated to v%1.').replace('%1', VERSION)
		if record.get('status') == 'failed':
			return _tr('The last update could not be installed (%1). Click Update Now to try again.').replace(
				'%1', str(record.get('reason') or '?'))
		return ''

	def checkupdate(self, popup_when_ready=False):
		"""在后台线程查最新版本，不在界面线程上联网（GitHub 连不上时，以前会把窗口卡住几十秒）。"""
		if self._check_inflight:
			return
		self._check_inflight = True
		self.lbl2.setText(_tr('Checking…'))
		self.lbl2.adjustSize()

		def worker():
			alertupdate = _tr('No Internet')
			ready = False
			info = None
			try:
				info = self.fetch_latest_release_info()
				result = (info or {}).get('tag')
				if result:
					# 只有严格更新的版本才算（开发版比最新发布还新时，不能提示“降级”）
					if is_newer_version(result, 'v' + VERSION):
						alertupdate = result + _tr(' is ready!')
						ready = True
					else:
						alertupdate = result + _tr(' (up-to-date)')
			except Exception:
				pass
			try:
				self.update_check_finished.emit(alertupdate, ready, popup_when_ready, info)
			except RuntimeError:
				pass   # 退出时窗口已销毁

		threading.Thread(target=worker, daemon=True, name='watermelon-update-check').start()

	def _on_update_check_finished(self, alertupdate, ready, popup_when_ready, info):
		self._check_inflight = False
		self.lbl2.setText(str(alertupdate or ''))
		self.lbl2.adjustSize()
		if not self._install_busy:
			self._update_available = bool(ready)
			self._release_info = dict(info) if (ready and isinstance(info, dict)) else None
			has_package = bool((self._release_info or {}).get('dmg_url'))
			self.install_btn.setEnabled(has_package)
			if ready and not has_package:
				self.install_status_lbl.setText(_tr('This release has no installer package; use the Github button.'))
		note = self._startup_note if popup_when_ready else ''
		if note and not self._install_busy:
			self._startup_note = ''
			self.install_status_lbl.setText(note)
		if popup_when_ready and (ready or note) and not self.isVisible():
			self.show()
			self.raise_()

	# ---- 一键安装 ----------------------------------------------------
	def start_install(self):
		if self._install_busy:
			# 下载期间同一个按钮显示“Cancel”
			if self._install_can_cancel and self._install_cancel is not None:
				self._install_cancel.set()
				self.install_btn.setEnabled(False)
				self.install_status_lbl.setText(_tr('Canceling…'))
			return
		info = dict(self._release_info or {})
		if not info.get('dmg_url'):
			return
		self._install_busy = True
		self._install_can_cancel = True
		self._install_cancel = threading.Event()
		self._download_started_at = 0.0
		self._download_started_bytes = 0
		self.install_btn.setText(_tr('Cancel'))
		self.install_progress_bar.set_fraction(0.0)
		self.install_progress_bar.show()
		self.install_status_lbl.setText(_tr('Connecting…'))
		threading.Thread(target=self._install_worker, args=(info, self._install_cancel),
						 daemon=True, name='watermelon-update-install').start()

	def _install_worker(self, info, cancel_event):
		last_emit = [0.0]

		def progress(done, total):
			now = time.monotonic()
			if now - last_emit[0] >= 0.1 or (total and done >= total):
				last_emit[0] = now
				self.install_progress.emit(int(done), int(total))

		try:
			dmg_path = watermelon_download_update_dmg(info, progress, cancel_event, status=self.install_status.emit)
			bundle = watermelon_running_app_bundle()
			blocker = watermelon_update_install_blocker(bundle)
			if blocker:
				# 这份没法替换自己：把校验过的 DMG 交给访达
				subprocess.Popen(['/usr/bin/open', dmg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				self.install_ready.emit({'manual': True, 'reason': blocker, 'dmg': dmg_path})
				return
			self.install_ready.emit(watermelon_stage_update(dmg_path, bundle, status=self.install_status.emit))
		except WatermelonUpdateError as exc:
			self.install_failed.emit(str(exc))
		except Exception as exc:
			logging.exception('One-click update failed.')
			self.install_failed.emit(_tr('Update failed: %1').replace('%1', str(exc)))

	def _on_install_progress(self, done, total):
		done, total = int(done or 0), int(total or 0)
		now = time.monotonic()
		if not self._download_started_at:
			self._download_started_at, self._download_started_bytes = now, done
		mb = 1024 * 1024
		text = _tr('Downloading… %1 / %2 MB').replace('%1', '%.1f' % (done / mb)).replace('%2', ('%.1f' % (total / mb)) if total else '?')
		elapsed = now - self._download_started_at
		if elapsed >= 1.0 and done > self._download_started_bytes:
			text += ' · %.1f MB/s' % ((done - self._download_started_bytes) / mb / elapsed)
		self.install_progress_bar.set_fraction(done / total if total else 0.0)
		self.install_status_lbl.setText(text)

	def _on_install_status(self, text):
		# 校验 / 挂载 / 复制 / 查签名：没有百分比，也不能再取消
		self._install_can_cancel = False
		self.install_btn.setEnabled(False)
		self.install_btn.setText(_tr('Installing…'))
		self.install_progress_bar.set_busy(True)
		self.install_status_lbl.setText(str(text or ''))

	def _reset_install_controls(self):
		self._install_busy = False
		self._install_can_cancel = False
		self._install_cancel = None
		self.install_progress_bar.set_busy(False)
		self.install_progress_bar.hide()
		self.install_btn.setText(_tr('Update Now'))
		self.install_btn.setEnabled(self._update_available and bool((self._release_info or {}).get('dmg_url')))

	def _on_install_failed(self, message):
		self._reset_install_controls()
		self.install_status_lbl.setText(str(message or ''))
		if not self.isVisible():
			self.show()

	def _on_install_ready(self, pending):
		pending = dict(pending or {})
		if pending.get('manual'):
			self._reset_install_controls()
			self.install_status_lbl.setText(
				_tr("Can't install automatically (%1). The installer is open: drag Watermelon into Applications.").replace(
					'%1', str(pending.get('reason', ''))))
			return
		global _WATERMELON_PENDING_UPDATE_INSTALL
		_WATERMELON_PENDING_UPDATE_INSTALL = pending
		self.install_progress_bar.set_fraction(1.0)
		self.install_status_lbl.setText(_tr('Restarting Watermelon to finish the update…'))
		if not self.isVisible():
			self.show()
		QTimer.singleShot(800, self._quit_for_install)

	def _quit_for_install(self):
		# 先让主窗口照常收尾（保存网页标签、停后台线程），再退出；替换在 app.exec() 返回后进行
		main = globals().get('w3')
		if main is not None:
			try:
				main.close()
			except Exception:
				pass
		app.quit()

	@classmethod
	def fetch_latest_release_info(cls):
		"""版本信息（版本号 + DMG）优先从接口取；接口不可用时，从发布页只取版本号
		（那样不能一键安装，Github 按钮照常可用）。"""
		try:
			info = watermelon_fetch_latest_release()
			if info:
				return info
		except Exception:
			pass
		tag = cls.extract_latest_tag(cls.fetch_latest_version_text())
		return {'tag': tag} if tag else None

	@staticmethod
	def fetch_latest_version_text():
		# 返回发布页的纯文本（接口不可用时的后备）
		targetURL = WATERMELON_UPDATE_RELEASES_URL
		try:
			s = requests.session()
			s.keep_alive = False
			response = s.get(targetURL, timeout=(4, 8))
			response.encoding = 'utf-8'
			html_content = response.text

			soup = BeautifulSoup(html_content, "html.parser")
			for img in soup.find_all("img"):
				img.decompose()
			text_maker = html2text.HTML2Text()
			text_maker.ignore_links = True
			text_maker.ignore_images = True
			plain_text = text_maker.handle(str(soup))
			plain_text_utf8 = plain_text.encode(response.encoding).decode("utf-8")

			for _ in range(10):
				plain_text_utf8 = (plain_text_utf8
								   .replace('\n\n\n\n', '\n\n')
								   .replace('\n\n\n', '\n\n')
								   .replace('   ', ' ')
								   .replace('  ', ' '))
			return plain_text_utf8
		except Exception:
			return None

	@staticmethod
	def extract_latest_tag(plain_text_utf8: str) -> str | None:
		# 返回类似 'v0.0.12' 的字符串
		if not plain_text_utf8:
			return None
		pattern2 = re.compile(r'(v\d+\.\d+\.\d+)\sLatest')
		result = pattern2.findall(plain_text_utf8)
		if result:
			return result[0]
		return None

# ── 和 Apple 备忘录互通的格式（2026-11-20 重做，见 watermelon_notes.py）──────────────────────────────
# Ryan："手动转译一些格式，但是不全…把所有的都加上…分隔线…超链接""图片和文件视频等重点是插入的位置要保持不变"
# "用替身没问题，改"。
# - 写：Markdown → 备忘录存得住的 HTML（引用 = 竖线 + 灰字、任务 = ☐ ☑ 这两个替身）；本地图片 / 文件 / 视频
#   经一个看不见的临时磁盘变成真正的附件，位置就在正文里写的地方。
# - 读：备忘录的 HTML → Markdown（分隔线、链接、行内代码、三级标题、多层列表、表格里的格式、附件按位置）。
# - 没在备忘录里改过的笔记：按“写完时正文的指纹”原样拿回当时的 Markdown，一个字符都不丢。
import watermelon_notes
import urllib.parse
import markdown_preview
# 预览页的公式引擎用自带的那一份（MathJax-2.7.9/，不联网；2026-11-25 从 2.7.1 升上来，修了 \unicode 能往页面里塞脚本的问题）；页面按“本地页面”装载，本地图片和它才读得到
markdown_preview.set_mathjax_folders(os.path.join(BasePath, 'MathJax-2.7.9'),
									 os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MathJax-2.7.9'))
LOCAL_PAGE_BASE = QUrl('file:///')

CACHE_DIR = Path(WATERMELON_CACHE_ROOT) / "NotesMarkdown"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
NOTE_MEMORY = watermelon_notes.NoteMemory(str(CACHE_DIR))
NOTES_ATTACHMENT_DIR = os.path.join(WATERMELON_DATA_DIR, 'Notes Attachments')   # 从备忘录取回的图片 / 文件


def strip_tags(text):
	return re.sub(r"<[^>]+>", "", text)


def normalize_ws(text):
	text = text.replace("&quot", '"')
	text = html_lib.unescape(text)
	text = text.replace("\u00a0", " ")
	return re.sub(r"\s+", " ", text).strip()


def markdown_to_html(md):
	"""Markdown → 预览用的 HTML 正文（见 markdown_preview.py）。"""
	return markdown_preview.render_markdown_body(md)


def _bionic_transform_text(text):
	if text is None:
		return ""
	esj = str(text)
	aj = jieba.cut(esj, cut_all=False)
	paj = '/'.join(aj)
	saj = paj.split('/')

	for i in range(len(saj)):
		item = str(saj[i])
		if not (re.search('[a-zA-Zａ-ｚＡ-Ｚ]', item) or re.search('[0-9０-９]', item) or any('\u4e00' <= ch <= '\u9fff' for ch in item)):
			continue
		if len(item) == 1:
			saj[i] = '**' + item + '**'
			continue
		if 'ing' in item:
			item = item.replace('ing', '**ing')
			item = item.replace('**ing**ing', 'ing**ing')
			lst = list(item)
			lst.insert(0, '**')
			saj[i] = ''.join(lst)
			continue
		if len(item) % 2 == 0:
			lst = list(item)
			half = len(item) // 2
			lst.insert(half, '**')
			lst.insert(0, '**')
			saj[i] = ''.join(lst)
			continue
		lst = list(item)
		lst.insert(0, '**')
		idx = int((len(item) + 1) / 2) + 1
		lst.insert(idx, '**')
		saj[i] = ''.join(lst)

	esj = ''.join(saj)
	i = 0
	while i <= len(esj) - 1:
		prev_ch = esj[i - 1] if i > 0 else ''
		if esj[i] in ('¥', '$') and not bool(re.search(r"\W", prev_ch)):
			esj = list(esj)
			esj.insert(i, ' ')
			esj = ''.join(esj)
			i += 2
			continue
		if esj[i] in ('%', '°'):
			if prev_ch == ' ':
				esj = list(esj)
				del esj[i - 1]
				esj = ''.join(esj)
				i -= 1
				continue
			esj = list(esj)
			esj.insert(i + 1, ' ')
			esj = ''.join(esj)
			i += 2
			continue
		i += 1

	i = 0
	while i >= 0 and i < len(esj) - 1:
		cur = esj[i]
		nxt = esj[i + 1]
		cur_zh = any('\u4e00' <= ch <= '\u9fff' for ch in cur)
		nxt_zh = any('\u4e00' <= ch <= '\u9fff' for ch in nxt)
		cur_en = bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', cur))
		nxt_en = bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', nxt))
		cur_num = bool(re.search('[0-9０-９]', cur))
		nxt_num = bool(re.search('[0-9０-９]', nxt))
		if (cur_zh and nxt_en) or (cur_zh and nxt_num) or (nxt_zh and cur_num) or (cur_num and nxt_en) or (nxt_num and cur_en) or (nxt_zh and cur_en):
			esj = list(esj)
			esj.insert(i + 1, ' ')
			esj = ''.join(esj)
			i += 1
			continue
		i += 1

	esj = esj.replace('  ', ' ')
	esj = esj.replace('****', '')
	return esj


_NOTES_STORE_NOTICE = {'told': False}
NOTES_STORE_WATCH = {'on': False}   # 主窗口盯着备忘录存储的文件时为真（那时后台不再定时去问）
NOTES_AUTOSAVE_DELAY_MS = 2000      # 停笔这么久自动存进备忘录


def _note_storage_key(folder, title, note_id=None):
	"""记“这张笔记上次同步时的样子”和放它的附件用的名字：有编号用编号（改标题也不变），否则文件夹 + 标题。"""
	return _note_id_for(folder, title, note_id) or f"{folder}/{title}"


def _load_note_markdown(folder, title, note_id=None):
	"""（Markdown, 存储指纹）。先只读备忘录自己的存储（不问备忘录，不到 0.01 秒）；这张笔记的存储记录和上次记下
	时一样 → 原样拿回当时的 Markdown。有表格的笔记要再问备忘录要一次正文（表格在存储里是另外的东西）。
	存储读不到时照旧问备忘录，指纹是空。找不到笔记返回 (None, '')。"""
	note_id = _note_id_for(folder, title, note_id)
	key = _note_storage_key(folder, title, note_id)
	state = watermelon_notes.note_state(folder, title, note_id)
	if state is not None:
		fingerprint, has_tables = state
		remembered = NOTE_MEMORY.recall(key, '', fingerprint=fingerprint)
		if remembered is not None:
			return remembered.strip(), fingerprint
		body = _read_note_html_from_notes(folder, title, note_id) if has_tables else None
		target = os.path.join(NOTES_ATTACHMENT_DIR, hashlib.sha256(key.encode('utf-8')).hexdigest()[:16])
		staging = target + '.new'
		shutil.rmtree(staging, ignore_errors=True)
		loaded = watermelon_notes.read_note_from_store(folder, title, note_id, attachments_dir=staging, body_html=body)
		if loaded is not None and loaded.get('markdown') is not None:
			md = loaded['markdown']
			if os.path.isdir(staging):
				shutil.rmtree(target, ignore_errors=True)
				os.rename(staging, target)
				md = md.replace(urllib.parse.quote(staging), urllib.parse.quote(target))
			NOTE_MEMORY.remember(key, '', md, fingerprint=loaded['fingerprint'])
			return md, loaded['fingerprint']
	html = _read_note_html_from_notes(folder, title, note_id)
	if not html:
		return None, ''
	if state is None and watermelon_notes.list_notes_from_store() is None:
		_tell_notes_store_needs_access()
	md = notes_html_to_markdown(html, cache_key=key, note_ref=(folder, title, note_id),
								fetch_attachments=lambda slots: _fetch_note_attachments(folder, title, slots, note_id))
	return md, ''


class NoteSaveWorker(QThread):
	"""在后台把一张笔记写进备忘录（写的时候可以继续打字）。done(成功, 写进去的 Markdown, 写完后的存储指纹, 出错原因)。"""
	done = pyqtSignal(bool, str, str, str)

	def __init__(self, folder, title, note_id, markdown_text, writer, parent=None):
		super().__init__(parent)
		self.folder, self.title, self.note_id, self.markdown_text, self.writer = folder, title, note_id, markdown_text, writer

	def run(self):
		try:
			self.writer(self.folder, self.title, watermelon_notes.markdown_to_notes_html(self.markdown_text), self.note_id)
			state = watermelon_notes.note_state(self.folder, self.title, self.note_id)
			if state is None and self.markdown_text.strip():
				# 标题这一行改了、又没有编号时，按新标题才找得到
				pass
			self.done.emit(True, self.markdown_text, state[0] if state else '', '')
		except Exception as exc:
			self.done.emit(False, self.markdown_text, '', str(exc))


def _tell_notes_store_needs_access():
	"""备忘录自己的存储读不到（没有“完全磁盘访问”）：这次运行里提醒一次，转换照常用备忘录给的正文。"""
	if _NOTES_STORE_NOTICE['told']:
		return
	_NOTES_STORE_NOTICE['told'] = True
	QTimer.singleShot(0, lambda: watermelon_alert(None, NAME, _tr(
		'To read check boxes, highlights, alignment and sub / superscript from notes that were changed in Notes, Watermelon needs "Full Disk Access" (System Settings › Privacy & Security › Full Disk Access). Without it these formats are read as plain text.')))


def notes_html_to_markdown(html, cache_key=None, fetch_attachments=None, note_ref=None):
	"""备忘录正文 → Markdown。正文和上次记下时一模一样（没在备忘录里改过）→ 原样拿回当时的 Markdown；
	否则转换：先读备忘录自己的存储（勾没勾、对齐、上下标、高亮只有那里有；note_ref =（文件夹, 标题）），
	读不到就用备忘录给的正文。fetch_attachments(个数) → 每个附件位置的 Markdown 引用（按正文里的顺序）。"""
	if not html:
		return ""
	if cache_key:
		remembered = NOTE_MEMORY.recall(cache_key, html)
		if remembered is not None:
			return remembered.strip()
	slots = watermelon_notes.count_attachment_slots(html)
	refs = []
	if slots and fetch_attachments is not None:
		try:
			refs = list(fetch_attachments(slots) or [])
		except Exception:
			logging.exception('Fetching the note\'s attachments failed.')
			refs = []
	md = None
	if note_ref is not None:
		md, reason = watermelon_notes.markdown_from_store(
			html, note_ref[0], note_ref[1], refs, note_id=_note_id_for(note_ref[0], note_ref[1], note_ref[2] if len(note_ref) > 2 else None))
		if md is None and reason == 'no-access':
			_tell_notes_store_needs_access()
	if md is None:
		md = watermelon_notes.notes_html_to_markdown(html, refs)
	if cache_key and (not slots or (len(refs) >= slots and all(refs[:slots]))):
		NOTE_MEMORY.remember(cache_key, html, md)   # 下次打开同一份正文不用再转换、再取附件
	return md


# 笔记的唯一编号（2026-11-20 Ryan：“如果你能找得到笔记的唯一编号，你就用那个唯一编号…现在这个读法最多只能用来
# 备用”）。备忘录给每张笔记一个不变的编号（AppleScript 的 id：x-coredata://…/ICNote/p数字，数字 = 它自己存储里的
# 行号）。列出笔记时就把编号带上，之后读、写、取附件都先按编号找；只有编号不管用（没有、或者那张笔记不在了）
# 才退回“账户/文件夹 + 标题”找第一条。同一个文件夹里同名的笔记、在备忘录里改了标题，都不再找错。
_NOTE_ID_BY_KEY = {}   # (文件夹, 标题) → 编号；同一个键有两张不同的笔记时是 ""


def _register_note_ids(notes):
	seen = {}
	for note in notes or []:
		if not isinstance(note, dict):
			continue
		key = ((note.get("folder") or "Unfiled").strip() or "Unfiled", note.get("title") or "(Untitled)")
		note_id = str(note.get("id") or "")
		seen[key] = note_id if key not in seen or seen[key] == note_id else ""
	_NOTE_ID_BY_KEY.clear()
	_NOTE_ID_BY_KEY.update(seen)
	return notes


def _note_id_for(folder, title, note_id=None):
	"""这张笔记的编号：手上有就用手上的，否则查列表里记的（那个文件夹里只有一张叫这个名字时才有）。"""
	if note_id:
		return str(note_id)
	return _NOTE_ID_BY_KEY.get(((folder or "Unfiled").strip() or "Unfiled", title or "(Untitled)"), "")


def _parse_notes_raw(raw):
	notes = []
	if raw:
		for item in raw.split(chr(31)):
			if not item:
				continue
			parts = item.split(chr(30), 1)
			folder_and_title = parts[0]
			body = parts[1] if len(parts) > 1 else ""
			folder_parts = folder_and_title.split(chr(29), 1)
			folder = folder_parts[0].strip() if folder_parts else "Unfiled"
			title = folder_parts[1].strip() if len(folder_parts) > 1 else folder_and_title.strip()
			notes.append({"folder": folder, "title": title, "body": body})
	return notes


# 旧的快照脚本：逐条笔记查询所在文件夹（每条约 5 次 Apple Event，100 条笔记要 6 秒多）。
# 现在只在快速脚本对不上时作为兜底。
_NOTES_LEGACY_SNAPSHOT_SCRIPT = """
	set AppleScript's text item delimiters to ASCII character 31
	tell application "Notes"
		set outList to {}
		repeat with n in notes
			set t to name of n
			set b to ""
			set f to "Unfiled"
			set accountName to ""
			try
				set c to container of n
				set cClass to class of c
				if cClass is folder then
					set f to name of c
					try
						set accountName to name of container of c
					end try
				else if cClass is account then
					set f to name of c
				end if
			on error
				try
					set f to name of folder of n
				end try
			end try
			if accountName is not "" then
				set f to accountName & "/" & f
			end if
			set end of outList to f & (ASCII character 29) & t & (ASCII character 30) & b
		end repeat
		set outText to outList as string
	end tell
	return outText
	"""

# 快速快照：一次请求取全部笔记的 id 和标题，再按文件夹（数量很少）各取一次笔记 id，
# 在 Python 里按 id 拼回“账户/文件夹”。结果（文件夹、标题、顺序）与旧脚本一致，
# 但只需零点几秒。Notes 的批量查询拿不到 container 的类型和 id，所以不能直接批量问每条笔记的容器。
_NOTES_FAST_SNAPSHOT_SCRIPT = r'''
on run
	set noteIds to {}
	set noteNames to {}
	set folderChunks to {}
	tell application "Notes"
		set noteIds to id of every note
		set noteNames to name of every note
		set allFolders to every folder
	end tell
	set AppleScript's text item delimiters to ASCII character 31
	repeat with fo in allFolders
		set f to "Unfiled"
		set accountName to ""
		set folderNoteIds to {}
		tell application "Notes"
			set f to name of fo
			try
				set accountName to name of container of fo
			end try
			set folderNoteIds to id of every note of fo
		end tell
		if accountName is not "" then set f to accountName & "/" & f
		set end of folderChunks to f & (ASCII character 29) & (folderNoteIds as string)
	end repeat
	set idsText to noteIds as string
	set namesText to noteNames as string
	set AppleScript's text item delimiters to ASCII character 30
	set foldersText to folderChunks as string
	set AppleScript's text item delimiters to ""
	return idsText & (ASCII character 28) & namesText & (ASCII character 28) & foldersText
end run
'''


def _parse_fast_notes_snapshot(raw):
	"""解析快速快照；只要有一条笔记找不到唯一的所在文件夹就返回 None，交给旧脚本兜底。"""
	sections = raw.rstrip("\n").split(chr(28))
	if len(sections) != 3:
		return None
	note_ids = sections[0].split(chr(31)) if sections[0] else []
	note_names = sections[1].split(chr(31)) if sections[1] else []
	if len(note_ids) != len(note_names):
		return None
	location_by_id = {}
	duplicated_ids = set()
	for chunk in (sections[2].split(chr(30)) if sections[2] else []):
		location, _, id_text = chunk.partition(chr(29))
		for note_id in (id_text.split(chr(31)) if id_text else []):
			if note_id in location_by_id:
				duplicated_ids.add(note_id)
			location_by_id[note_id] = location
	notes = []
	for note_id, name in zip(note_ids, note_names):
		if note_id in duplicated_ids or note_id not in location_by_id:
			return None
		notes.append({"folder": location_by_id[note_id].strip(), "title": name.strip(), "body": "", "id": note_id})
	return _register_note_ids(notes)


def _run_notes_snapshot_script(script):
	result = subprocess.run(
		["osascript", "-e", script],
		capture_output=True,
		text=True,
		check=False,
	)
	if result.returncode != 0:
		message = result.stderr.strip() or _tr("Unknown AppleScript error.")
		raise RuntimeError(message)
	return result.stdout


def _fetch_notes_snapshot():
	"""取所有笔记的文件夹、标题、编号（不含正文）。先直接读备忘录自己的存储（不到 0.01 秒，结果和问备忘录的
	一样：2026-11-21 在 264 张笔记上逐张比对过编号、文件夹、标题）；读不到（没有完全磁盘访问）才去问备忘录
	（约 0.7 秒）。"""
	from_store = watermelon_notes.list_notes_from_store()
	if from_store is not None:
		return _register_note_ids(from_store)
	try:
		notes = _parse_fast_notes_snapshot(_run_notes_snapshot_script(_NOTES_FAST_SNAPSHOT_SCRIPT))
	except Exception:
		notes = None
	if notes is not None:
		return notes
	raw = _run_notes_snapshot_script(_NOTES_LEGACY_SNAPSHOT_SCRIPT).rstrip("\n")
	return _parse_notes_raw(raw)


# 按“文件夹 + 标题”找一条笔记。先让 Notes 用 whose 按标题筛选（一次请求），
# 再在少数候选里核对文件夹；找不到时退回旧的逐条遍历，匹配规则不变。
# 旧写法每次都遍历全部笔记，越靠后的笔记越慢（100 条时约 1 秒）。
_NOTE_LOOKUP_HANDLERS = r'''
on noteFolderPath(n)
	set f to "Unfiled"
	set accountName to ""
	tell application "Notes"
		try
			set c to container of n
			set cClass to class of c
			if cClass is folder then
				set f to name of c
				try
					set accountName to name of container of c
				end try
			else if cClass is account then
				set f to name of c
			end if
		on error
			try
				set f to name of folder of n
			end try
		end try
	end tell
	if accountName is not "" then
		set f to accountName & "/" & f
	end if
	return f
end noteFolderPath

on findNoteIn(candidates, targetFolder, targetTitle)
	repeat with n in candidates
		tell application "Notes" to set t to name of n
		if t is equal to targetTitle then
			if targetFolder is "" then return contents of n
			if my noteFolderPath(n) is equal to targetFolder then return contents of n
		end if
	end repeat
	return missing value
end findNoteIn

on findNoteWithId(noteId, targetFolder, targetTitle)
	if noteId is not "" then
		try
			tell application "Notes"
				set idNote to note id noteId
				set idName to name of idNote
			end tell
			return idNote
		end try
	end if
	return my findNote(targetFolder, targetTitle)
end findNoteWithId

on noteIdArg(argv, position)
	if (count of argv) ≥ position then return item position of argv
	return ""
end noteIdArg

on findNote(targetFolder, targetTitle)
	try
		tell application "Notes" to set candidates to (every note whose name is targetTitle)
		set targetNote to my findNoteIn(candidates, targetFolder, targetTitle)
		if targetNote is not missing value then return targetNote
	end try
	tell application "Notes" to set candidates to every note
	return my findNoteIn(candidates, targetFolder, targetTitle)
end findNote
'''

_NOTE_READ_SCRIPT = _NOTE_LOOKUP_HANDLERS + r'''
on run argv
	set targetNote to my findNoteWithId(my noteIdArg(argv, 3), item 1 of argv, item 2 of argv)
	if targetNote is missing value then return ""
	tell application "Notes" to return body of targetNote
end run
'''

_NOTE_WRITE_SCRIPT = _NOTE_LOOKUP_HANDLERS + r'''
on run argv
	set targetFolder to item 1 of argv
	set targetTitle to item 2 of argv
	set filePath to item 3 of argv
	set newHTML to (do shell script "cat " & quoted form of filePath)
	set targetNote to my findNoteWithId(my noteIdArg(argv, 4), targetFolder, targetTitle)
	if targetNote is missing value then error "NOT_FOUND"
	tell application "Notes" to set body of targetNote to newHTML
end run
'''


# 把一张笔记的附件按正文里的顺序存出来（表格在备忘录里也算附件，但没有名字，跳过）。PDF 之类要过几秒才
# 出现在列表里，所以最多等十几秒，等到个数和正文里的位置数对上。存成 1、2、3…，名字另外返回。
_NOTE_SAVE_ATTACHMENTS_SCRIPT = _NOTE_LOOKUP_HANDLERS + r'''
on run argv
	set outDir to item 3 of argv
	set wanted to (item 4 of argv) as integer
	set targetNote to my findNoteWithId(my noteIdArg(argv, 5), item 1 of argv, item 2 of argv)
	if targetNote is missing value then return ""
	tell application "Notes"
		repeat 24 times
			set readyCount to 0
			repeat with a in attachments of targetNote
				if (name of a) is not missing value then set readyCount to readyCount + 1
			end repeat
			if readyCount ≥ wanted then exit repeat
			delay 0.5
		end repeat
		set out to ""
		set i to 0
		repeat with a in attachments of targetNote
			set nm to name of a
			if nm is not missing value then
				set i to i + 1
				try
					save a in POSIX file (outDir & "/" & i)
					set out to out & i & tab & nm & linefeed
				on error
					set out to out & i & tab & linefeed
				end try
			end if
		end repeat
		return out
	end tell
end run
'''


def _fetch_note_attachments(folder, title, slots, note_id=None):
	"""这张笔记的附件存到 数据文件夹/Notes Attachments/<这张笔记>/f1、f2…/，返回每个位置的 Markdown 引用（存不出来的是空）。"""
	note_key = f"{folder}/{title}"
	target = os.path.join(NOTES_ATTACHMENT_DIR, hashlib.sha256(note_key.encode('utf-8')).hexdigest()[:16])
	staging = target + '.new'
	shutil.rmtree(staging, ignore_errors=True)
	os.makedirs(staging, exist_ok=True)
	# 先按备忘录自己存储里的位置直接拿文件（画的图、有时不在脚本列表里的 PDF 都在，位置不会错开）
	note_id = _note_id_for(folder, title, note_id)
	from_store = watermelon_notes.fetch_attachments_from_store(folder, title, staging, note_id=note_id)
	if from_store is not None:
		shutil.rmtree(target, ignore_errors=True)
		os.rename(staging, target)
		return [ref.replace(urllib.parse.quote(staging), urllib.parse.quote(target)) for ref in from_store]
	listing = subprocess.check_output(["osascript", "-e", _NOTE_SAVE_ATTACHMENTS_SCRIPT, folder, title, staging, str(int(slots)), note_id],
									  text=True, timeout=180)
	names = []
	for line in listing.split('\n'):
		if '\t' not in line:
			continue
		number, name = line.split('\t', 1)
		source = os.path.join(staging, number)
		name = name.strip().replace('/', '_')
		if name and os.path.isfile(source):
			# 每个附件放在自己编号的小文件夹里，文件名保持原样（再写回备忘录时名字不会越变越长）
			holder = os.path.join(staging, 'f' + number)
			os.makedirs(holder, exist_ok=True)
			os.rename(source, os.path.join(holder, name))
			names.append(os.path.join('f' + number, name))
		else:
			names.append('')
	shutil.rmtree(target, ignore_errors=True)   # 上一次取回的那一批
	os.rename(staging, target)
	return [watermelon_notes.attachment_reference(os.path.join(target, final), os.path.basename(final)) if final else ''
			for final in names]


def _read_note_html_from_notes(folder, title, note_id=None):
	try:
		return subprocess.check_output(["osascript", "-e", _NOTE_READ_SCRIPT, folder, title, _note_id_for(folder, title, note_id)], text=True)
	except Exception:
		return ""


def _frontmost_app_kind_unpooled():
	front = NSWorkspace.sharedWorkspace().frontmostApplication()
	if front is None:
		return ""
	if int(front.processIdentifier()) == os.getpid() or str(front.localizedName() or "") == NAME:
		return "watermelon"
	if str(front.bundleIdentifier() or "") == "com.apple.Notes":
		return "notes"
	return ""


def _frontmost_app_kind():
	"""前台应用是本程序返回 'watermelon'，是备忘录返回 'notes'，否则返回 ''。"""
	if NSWorkspace is None:
		return ""
	try:
		if objc is not None and hasattr(objc, "autorelease_pool"):
			with objc.autorelease_pool():
				return _frontmost_app_kind_unpooled()
		return _frontmost_app_kind_unpooled()
	except Exception:
		return ""


def _write_notes_cache(notes, cache_path=NOTES_CACHE_PATH):
	dir_path = os.path.dirname(cache_path)
	if dir_path and not os.path.exists(dir_path):
		os.makedirs(dir_path, exist_ok=True)
	notes_summary = []
	for note in notes:
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		entry = {"folder": folder, "title": title, "id": str(note.get("id") or "")}
		if note.get("created") is not None:
			entry["created"] = note["created"]        # 新建时间：选笔记的列表按它新的在上
		notes_summary.append(entry)
	payload = {"updated_at": time.time(), "notes": notes_summary}
	tmp_path = f"{cache_path}.tmp"
	with open(tmp_path, "w", encoding="utf-8") as f0:
		json.dump(payload, f0, ensure_ascii=False)
	os.replace(tmp_path, cache_path)


def _read_notes_cache(cache_path=NOTES_CACHE_PATH):
	try:
		with open(cache_path, "r", encoding="utf-8") as f0:
			payload = json.load(f0)
	except FileNotFoundError:
		return [], _tr("Notes cache not ready.")
	except Exception as exc:
		return [], _tr("Notes cache read failed: %1").replace("%1", str(exc))
	if isinstance(payload, dict):
		notes = payload.get("notes", [])
	elif isinstance(payload, list):
		notes = payload
	else:
		notes = []
	return _register_note_ids(notes), None


class NotesCacheWorker(QThread):
	error = pyqtSignal(str)
	updated = pyqtSignal(int)

	# Notes 模式下、Watermelon 或备忘录在前台时的扫描间隔；其余情况用较长间隔
	ACTIVE_INTERVAL_SECONDS = 3
	IDLE_INTERVAL_SECONDS = 15

	def __init__(self, cache_path=NOTES_CACHE_PATH, parent=None):
		super().__init__(parent)
		self.cache_path = cache_path
		self._running = True
		self._wake_event = threading.Event()

	def stop(self):
		self._running = False
		self._wake_event.set()

	def request_refresh(self):
		"""不等间隔结束，马上开始下一轮扫描。"""
		self._wake_event.set()

	def _sleep(self, seconds):
		self._wake_event.wait(seconds)
		self._wake_event.clear()

	def run(self):
		while self._running:
			try:
				parent = self.parent()
				if parent and getattr(parent, "notes_refresh_in_progress", False):
					self._sleep(self._next_interval_seconds())
					continue
				notes = _fetch_notes_snapshot()
				_write_notes_cache(notes, self.cache_path)
				self.updated.emit(len(notes))
			except Exception as exc:
				self.error.emit(str(exc))
			if not self._running:
				return
			self._sleep(self._next_interval_seconds())

	def _next_interval_seconds(self):
		parent = self.parent()
		if NOTES_STORE_WATCH['on']:
			return None   # 不轮询：备忘录的存储一变，文件系统会通知（window3._on_notes_store_changed），那时才叫醒
		notes_mode = bool(getattr(parent, "notes_mode_enabled", False)) if parent else False
		if notes_mode and _frontmost_app_kind() in ("watermelon", "notes"):
			return self.ACTIVE_INTERVAL_SECONDS
		return self.IDLE_INTERVAL_SECONDS


class NotesLoader(QThread):
	finished = pyqtSignal(list)
	error = pyqtSignal(str)

	def run(self):
		# 只取文件夹和标题。以前这里还会读出每条笔记的正文（100 条要 8 秒以上、几 MB 输出），
		# 但切换后当前笔记的正文本来就会单独重读一次，其余笔记在被选中时再读。
		try:
			notes = _fetch_notes_snapshot()
		except Exception as exc:
			self.error.emit(str(exc) or _tr("Unknown AppleScript error."))
			return
		self.finished.emit(notes)


class NoteHtmlReadWorker(QThread):
	"""在后台读一条笔记的正文，避免 osascript 卡住界面。"""
	result = pyqtSignal(str, str, str)  # folder, title, html

	def __init__(self, folder, title, parent=None):
		super().__init__(parent)
		self.folder = folder
		self.title = title

	def run(self):
		self.result.emit(self.folder, self.title, _read_note_html_from_notes(self.folder, self.title) or "")


class PreviewRenderWorker(QThread):
	rendered = pyqtSignal(int, object, object)
	failed = pyqtSignal(int, str)

	def __init__(self, request_id, markdown_text, render_left, render_right, parent=None):
		super().__init__(parent)
		self.request_id = request_id
		self.markdown_text = markdown_text
		self.render_left = render_left
		self.render_right = render_right

	def run(self):
		try:
			left_html = None
			right_html = None
			# 打字时的预览：每一块排好的结果都记着，打一个字只重排那一块（长文档从几百毫秒降到一两毫秒；
			# 结果和整篇排版一样，见 markdown_preview.render_markdown_body_quick / bionic_html）
			if self.render_left:
				left_html = markdown_preview.render_markdown_body_quick(self.markdown_text)
			if self.isInterruptionRequested():
				return
			if self.render_right:
				# 右边的“加粗阅读”：先照常排好，再只给文字加粗（公式、代码、表格、任务框都不动）
				right_html = markdown_preview.bionic_html(left_html if left_html is not None else markdown_preview.render_markdown_body_quick(self.markdown_text),
														  _bionic_transform_text)
			if self.isInterruptionRequested():
				return
			self.rendered.emit(self.request_id, left_html, right_html)
		except Exception as exc:
			self.failed.emit(self.request_id, str(exc))


class NotesFolderDialog(CustomMessageBox):
	note_selected = pyqtSignal(object)

	def __init__(self):
		super().__init__(text=None, buttons=(), fixed_size=None)
		# 样式书 5.7 / 5.10「对话框」：玻璃对话框（底子在 CustomMessageBox），宽 = 批准宽度，出现在主窗口上方
		self.setWindowTitle(_tr("Select Notes"))
		self.resize(520, 360)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
		self.body_layout.setContentsMargins(20, 18, 20, 16)
		self.body_layout.setSpacing(12)

		self.notes = []
		self.filtered_notes = []
		self.folder_ids = []
		self.active_folder = None

		self.status_label = QLabel(_tr("Ready."))
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText(_tr("Filter notes by title..."))
		self.search_input.setClearButtonEnabled(True)
		self.search_input.textChanged.connect(self.apply_filter)
		# 搜的是这一整个对话框 → 全局搜索 = 玻璃胶囊、高 36、画出来的放大镜（样式书 5.5 A）
		self._style_search_input()
		glass_search_field(self.search_input)

		self.folder_list = QListWidget()
		self.folder_list.currentRowChanged.connect(self.on_folder_changed)

		self.list_widget = QListWidget()
		self.list_widget.itemDoubleClicked.connect(self.select_current)

		splitter = QSplitter(Qt.Orientation.Horizontal)
		splitter.addWidget(self.folder_list)
		splitter.addWidget(self.list_widget)
		splitter.setStretchFactor(0, 1)
		splitter.setStretchFactor(1, 2)

		# 对话框里的按钮 = 灰色普通按钮，靠右，最小宽 96；回车 = 选中，Esc = 取消（样式书 5.1 / 5.7）
		cancel_btn = MacNormalButton(_tr("Cancel"))
		cancel_btn.setMinimumWidth(96)
		cancel_btn.clicked.connect(self.reject)
		select_btn = MacNormalButton(_tr("Select"))
		select_btn.setMinimumWidth(96)
		select_btn.clicked.connect(self.select_current)
		self.search_input.returnPressed.connect(self.select_current)

		btn_row = QHBoxLayout()
		btn_row.setContentsMargins(0, 4, 0, 0)
		btn_row.setSpacing(8)
		btn_row.addStretch()
		btn_row.addWidget(cancel_btn)
		btn_row.addWidget(select_btn)

		w3 = QWidget()
		blay3 = QVBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.setSpacing(10)
		blay3.addWidget(self.status_label)
		blay3.addWidget(self.search_input)
		blay3.addWidget(splitter)
		blay3.addLayout(btn_row)
		w3.setLayout(blay3)
		#w3.setObjectName("Main")

		self.body_layout.addWidget(w3)

	# def showEvent(self, event):
	# 	super().showEvent(event)
	# 	if self._centered_once:
	# 		return
	# 	screen = QGuiApplication.screenAt(QCursor.pos())
	# 	if not screen:
	# 		if self.parent() and hasattr(self.parent(), "screen"):
	# 			screen = self.parent().screen()
	# 		else:
	# 			screen = QGuiApplication.primaryScreen()
	# 	if screen:
	# 		geo = screen.availableGeometry()
	# 		x = geo.x() + int((geo.width() - self.width()) / 2)
	# 		y = geo.y() + int((geo.height() - self.height()) / 2)
	# 		self.move(x, y)
	# 	self._centered_once = True

	def _style_search_input(self):
		dark = is_dark_theme(app)
		self.search_input.setStyleSheet(
			'QLineEdit { border: none; border-radius: 18px; padding: 0px 16px 0px 4px; font-size: 15px;'
			' background-color: %s; color: %s; }' % (('#3A3A3A', '#F2F2F7') if dark else ('#F5F6F8', '#20242B')))

	def changeEvent(self, event):
		super().changeEvent(event)
		if event.type() == QEvent.Type.ApplicationPaletteChange and hasattr(self, 'search_input'):
			self._style_search_input()

	def set_status(self, text):
		self.status_label.setText(text)

	def set_notes(self, notes):
		self.notes = notes
		self.populate_folders()
		self.apply_filter(self.search_input.text())
		if notes:
			self.set_status(_tr("Select a note:"))
		else:
			self.set_status(_tr("No notes found."))

	def populate_folders(self):
		folders = sorted(
			{
				(note.get("folder") or "Unfiled").strip() or "Unfiled"
				for note in self.notes
			}
		)
		self.folder_ids = [None] + folders
		self.folder_list.blockSignals(True)
		self.folder_list.clear()
		self.folder_list.addItem(_tr("All Notes"))
		for folder in folders:
			self.folder_list.addItem(folder)
		self.folder_list.blockSignals(False)
		if self.folder_ids:
			self.folder_list.setCurrentRow(0)

	def on_folder_changed(self, index):
		if index < 0 or index >= len(self.folder_ids):
			self.active_folder = None
		else:
			self.active_folder = self.folder_ids[index]
		self.apply_filter(self.search_input.text())

	def _newest_first(self):
		"""新建的笔记在最上面（Ryan 2026-11-24：“现在把最老的笔记放在最上面…把最新建的那个笔记放在上面，不然每次都要
		滚到最底下”）。不知道新建时间的（读不到备忘录自己的存储时）排在后面、保持原来的顺序。"""
		return sorted(self.notes, key=lambda note: (0, -float(note["created"])) if note.get("created") is not None else (1, 0.0))

	def apply_filter(self, text):
		query = text.strip().lower()
		self.filtered_notes = []
		for note in self._newest_first():
			folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
			if self.active_folder and folder != self.active_folder:
				continue
			title = note.get("title") or ""
			if query and query not in title.lower():
				continue
			self.filtered_notes.append(note)
		self.list_widget.clear()
		for note in self.filtered_notes:
			title = note.get("title") or "(Untitled)"
			self.list_widget.addItem(title)
		if self.filtered_notes:
			self.list_widget.setCurrentRow(0)

	def select_current(self):
		index = self.list_widget.currentRow()
		if index < 0 or index >= len(self.filtered_notes):
			return
		note = self.filtered_notes[index]
		self.note_selected.emit(note)
		self.accept()
	
	def center(self):  # 设置窗口居中
		screen = QGuiApplication.primaryScreen()
		if screen:
			geo = screen.availableGeometry()
			x = geo.x() + (geo.width() - self.width()) // 2
			y = geo.y() + (geo.height() - self.height()) // 2
			self.move(x, y)


# =====================================================================
# 网页模式（Web）
# 标签栏移植自 Broccoli（NavSitePill → WebSitePill、WebNavBar → WebTabBar、_IconFetcher），
# 面板是 Broccoli WebViewPanel 的精简版。与 Broccoli 不同的三处：
#   1. “新窗口 / 弹窗”开成新标签页并保留 window.opener（Google、微软的登录弹窗要靠它回传）；
#      Broccoli 是在当前标签里打开、丢掉新窗口请求。
#   2. 重启后恢复的是每个标签页“当前所在”的网址，而不是最初打开的网址。
#   3. 下载走保存对话框；“存到本地 / Notes”时用同一个下载通道悄悄抓取 Google 的导出文件。
# =====================================================================

WEB_TAB_BLANK_LABEL = _tr('New Tab')
WEB_CAPTURE_PREFIX = 'wmcap_'
WEB_START_SHORTCUTS = (
	('Google Docs', 'https://docs.google.com/document/u/0/', '#4285F4'),
	('Google Slides', 'https://docs.google.com/presentation/u/0/', '#F4B400'),
	('Microsoft Word', 'https://www.office.com/launch/word', '#2B579A'),
)

# 网页输入法脚本（所有网站、所有框架，不按网址分流）。两件事：
# 1) 输入法中转的焦点报告：打字的框在“和主页面不同来源”的内嵌框架里时，告诉 Watermelon 是哪个框架
#    （这种框架可能跑在单独进程里，QtWebEngine 不把输入法的组合文字送进去，见下方 WebImeBridge 处说明）。
#    网页里看不出一个框架是不是单独进程，只能看来源：来源不同就中转（宁可多中转，也不让输入法打不进字）。
# 2) 补发 229 按键（默认停用，WEB_IME_PATCH_229）：
#    macOS 上 QtWebEngine 有个老问题（QTBUG-85563 / QTBUG-53638）：输入法接手的按键，网页一个“按键按下/抬起”都收不到，
#    只收到组合事件；真正的 Chrome / Safari 会先发键码 229（"Process"）的按下，再发抬起。
#    当初为 Word 网页版加的，后来查明 Word 打不进字的真因是单独进程的框架收不到组合文字（已由中转解决），
#    有了中转后 Word 的框架里根本没有组合事件，补发不会触发，所以停用。代码保留，需要时把开关改回 True。
#    EditContext 编辑器的组合事件发生在 EditContext 对象上，补发要在页面创建 EditContext 时先挂监听，
#    所以脚本必须注入页面自己的脚本环境（MainWorld）。
# 以前只对微软 Office 站点生效（按网址名单），已改成上面的按条件判断：
# WEB_IME_SHIM_HOST_PATTERN = (
# 	r'(^|\.)(officeapps\.live\.com|cloud\.microsoft|office\.com|office365\.com|'
# 	r'microsoft365\.com|sharepoint\.com|onedrive\.live\.com|live\.com)$'
# )
WEB_IME_PATCH_229 = False
# 诊断记录：只记事件类型、是否真实按键、是否补发、所在站点，不记任何文字内容和普通按键的键码。
# 写到数据文件夹的 ime_debug.log（超过 1 MB 自动清空重写）。问题解决后可关掉。
# WEB_IME_DEBUG_LOG = True   # 需要再排查输入法问题时，打开这一行、注释掉下一行
WEB_IME_DEBUG_LOG = False
WEB_IME_DEBUG_PREFIX = '[WM-IME] '
WEB_IME_FOCUS_PREFIX = '[WM-IMEFOCUS] '
WEB_IME_KEYDOWN_SHIM_JS = r"""(function () {
	if (window.__watermelonImeShim) return;
	window.__watermelonImeShim = true;
	var DEBUG = %(debug)s;
	var PATCH_229 = %(patch229)s;
	function log(s) {
		if (!DEBUG) return;
		try { console.log(%(prefix)s + location.hostname + ' | ' + s); } catch (err) {}
	}
	var lastRealProcessKey = 0;
	function codeOf(e) { return (e.keyCode === 229 || e.key === 'Process') ? '229' : 'other'; }
	if (PATCH_229 || DEBUG) {
		window.addEventListener('keydown', function (e) {
			if (e.isTrusted && codeOf(e) === '229') lastRealProcessKey = Date.now();
			log('keydown ' + codeOf(e) + (e.isTrusted ? ' real' : ' patched') + (e.isComposing ? ' composing' : ''));
		}, true);
	}
	function describe(el) {
		// 只描述元素种类和能否编辑，不读取任何内容
		if (!el) return 'none';
		var d = String(el.tagName || '?').toLowerCase();
		if (el.isContentEditable) d += ' editable';
		if (el.editContext) d += ' editcontext';
		if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') d += ' text-field';
		try { var im = el.getAttribute && el.getAttribute('inputmode'); if (im) d += ' inputmode=' + im; } catch (err) {}
		try { var r = el.getBoundingClientRect(); d += ' size=' + Math.round(r.width) + 'x' + Math.round(r.height); } catch (err) {}
		return d;
	}
	if (DEBUG) {
		window.addEventListener('keyup', function (e) {
			log('keyup ' + codeOf(e) + (e.isTrusted ? ' real' : ' patched') + ' focus=' + describe(document.activeElement));
		}, true);
		window.addEventListener('beforeinput', function (e) { log('beforeinput ' + e.inputType); }, true);
		window.addEventListener('input', function (e) { log('input ' + (e.inputType || '')); }, true);
		window.addEventListener('focusin', function (e) { log('focusin ' + describe(e.target)); }, true);
		window.addEventListener('focusout', function (e) { log('focusout ' + describe(e.target)); }, true);
		window.addEventListener('textInput', function () { log('textInput'); }, true);
	}
	// 输入法中转：打字的框在“和主页面不同来源”的内嵌框架里时，告诉 Watermelon 是哪个框架（所有网站同一个规则）
	var isTopFrame = (window.top === window);
	var otherOrigin = false;
	if (!isTopFrame) {
		try { void window.top.location.href; } catch (err) { otherOrigin = true; }   // 读不到主页面地址 = 来源不同
	}
	function isEditable(el) {
		if (!el) return false;
		if (el.isContentEditable || el.tagName === 'TEXTAREA') return true;
		return el.tagName === 'INPUT' && /^(text|search|url|email|tel|password|)$/i.test(el.type || '');
	}
	function reportFocus(state) {
		try { console.log(%(focus_prefix)s + state + ' ' + location.href); } catch (err) {}
	}
	if (otherOrigin) {
		window.addEventListener('focusin', function (e) {
			if (isEditable(e.target)) { window.__watermelonLastEditable = e.target; reportFocus('in'); }
		}, true);
		window.addEventListener('focusout', function (e) {
			if (isEditable(e.target)) reportFocus('out');
			var box = document.getElementById('__watermelon_ime_preview');
			if (box) box.style.display = 'none';
		}, true);
		// 编辑器常把焦点弹走再拿回来；在编辑框里按键/点击时再报一次，保证中转不断
		var reannounce = function () {
			var a = document.activeElement;
			if (isEditable(a)) { window.__watermelonLastEditable = a; reportFocus('in'); }
		};
		window.addEventListener('keyup', reannounce, true);
		window.addEventListener('pointerdown', function () { setTimeout(reannounce, 0); }, true);
		if (isEditable(document.activeElement) && document.hasFocus()) reportFocus('in');
	} else {
		// 主页面或同来源框架里的输入框拿到焦点（输入法本来就正常）：告诉 Watermelon 停止中转，免得把字送进别的框架
		window.addEventListener('focusin', function (e) { if (isEditable(e.target)) reportFocus('top'); }, true);
	}
	function fire(type, target, composing) {
		try {
			target.dispatchEvent(new KeyboardEvent(type, {
				key: 'Process', code: '', keyCode: 229, which: 229,
				isComposing: composing, bubbles: true, cancelable: true, composed: true
			}));
		} catch (err) {}
	}
	function processKey(target, composing, why) {
		if (!target) return;
		if (Date.now() - lastRealProcessKey < 80) return;   // 引擎已经发过真的 229
		log('patching 229 before ' + why);
		fire('keydown', target, composing);
		setTimeout(function () { fire('keyup', target, composing); }, 0);
	}
	function focusedElement() {
		var a = document.activeElement;
		while (a && a.shadowRoot && a.shadowRoot.activeElement) a = a.shadowRoot.activeElement;
		return a || document.body;
	}
	if (PATCH_229) {
	// 普通编辑器：组合事件发生在网页元素上
	var domFirstUpdatePending = false;
	window.addEventListener('compositionstart', function (e) {
		log('dom compositionstart');
		processKey(e.target, false, 'dom compositionstart');      // 第一个键：先 keydown(229)，再 compositionstart
		domFirstUpdatePending = true;
	}, true);
	window.addEventListener('compositionupdate', function (e) {
		if (domFirstUpdatePending) { domFirstUpdatePending = false; return; }   // 和 compositionstart 同属第一个键
		processKey(e.target, true, 'dom compositionupdate');
	}, true);
	window.addEventListener('compositionend', function (e) {
		log('dom compositionend');
		domFirstUpdatePending = false;
		processKey(e.target, true, 'dom compositionend');          // 确认键（回车/空格）
	}, true);
	// EditContext 编辑器（Word 网页版）：组合事件发生在 EditContext 对象上；在创建时先挂监听，排在 Word 自己的监听前面
	if (typeof window.EditContext === 'function') {
		var OriginalEditContext = window.EditContext;
		var hookEditContext = function (ec) {
			var composing = false, firstUpdatePending = false;
			log('EditContext created');
			ec.addEventListener('compositionstart', function () {
				log('editcontext compositionstart');
				composing = true; firstUpdatePending = true;
				processKey(focusedElement(), false, 'editcontext compositionstart');
			});
			ec.addEventListener('textupdate', function () {
				if (!composing) { log('editcontext textupdate (no composition)'); return; }
				if (firstUpdatePending) { firstUpdatePending = false; return; }
				processKey(focusedElement(), true, 'editcontext textupdate');
			});
			ec.addEventListener('compositionend', function () {
				log('editcontext compositionend');
				composing = false; firstUpdatePending = false;
				processKey(focusedElement(), true, 'editcontext compositionend');
			});
		};
		var WrappedEditContext = function EditContext(init) {
			var ec = (init === undefined) ? new OriginalEditContext() : new OriginalEditContext(init);
			try { hookEditContext(ec); } catch (err) {}
			return ec;
		};
		WrappedEditContext.prototype = OriginalEditContext.prototype;
		window.EditContext = WrappedEditContext;
	}
	}   // PATCH_229
	log('shim ready, EditContext available: ' + (typeof window.EditContext === 'function'));
})();"""

# 输入法候选框位置（所有站点，按编辑器种类分流，不按网址）
# 输入法靠“光标在屏幕哪里”来摆候选框。网页引擎只认网页里普通的文字选区（输入框、可编辑区），
# 不认 EditContext 这类“自管输入”的编辑器自己报的光标位置（真 Chrome 认）。这类编辑器的普通选区
# 要么不存在、要么停在无关的地方，于是候选框跑到窗口左上角或编辑区的角上。
# 这个脚本只在“焦点所在的元素用了 EditContext”时起作用：记下编辑器报给浏览器的光标位置，
# 报给 Watermelon（只报坐标，不读任何文字）；Watermelon 再把它转告输入法。
# 普通输入框、普通可编辑区不受影响，仍用引擎自己的光标位置。只记录、不改变编辑器的任何行为。
# Google Docs（服务器开了开关时）就是这种编辑器：在主页面创建 EditContext，却挂在隐藏内嵌框架里的元素上，
# 所以要从主页面的焦点一路找进同源内嵌框架。坐标照 Chromium 的规矩：编辑器报的就是整页视口坐标，不加框架偏移
# （edit_context.cc 里只乘缩放比例）。只由创建这个 EditContext 的页面来报（记录在它那里）；跨站框架里不报。
WEB_IME_CARET_PREFIX = '[WM-IMECARET] '
WEB_IME_CARET_JS = r"""(function () {
	if (window.__watermelonImeCaret) return;
	window.__watermelonImeCaret = true;
	var EC = window.EditContext;
	if (typeof EC !== 'function' || !EC.prototype) return;
	try { if (window.top !== window) void window.top.location.href; } catch (err) { return; }   // 跨站框架
	var proto = EC.prototype;
	var selection = new WeakMap();   // EditContext → 编辑器最后一次报的光标框
	var pending = false, last = 'none';
	function deepActive() {
		// 焦点可能在同源内嵌框架或影子树里，一路找到真正的焦点元素
		var a = document.activeElement;
		for (var depth = 0; a && depth < 10; depth++) {
			if (a.shadowRoot && a.shadowRoot.activeElement) { a = a.shadowRoot.activeElement; continue; }
			if (a.tagName === 'IFRAME' || a.tagName === 'FRAME') {
				var d = null;
				try { d = a.contentDocument; } catch (err) {}
				if (!d || !d.activeElement) break;
				a = d.activeElement;
				continue;
			}
			break;
		}
		return a;
	}
	function caretRect(ec) {
		var s = selection.get(ec);
		if (s && s.height > 0) return s;
		try {
			var list = ec.characterBounds(), at = ec.selectionStart - ec.characterBoundsRangeStart;
			if (list && list.length && at >= 0) {
				if (at >= list.length) { var e = list[list.length - 1]; return {left: e.right, top: e.top, width: 1, height: e.height}; }
				var c = list[at];
				return {left: c.left, top: c.top, width: 1, height: c.height};
			}
		} catch (err) {}
		return null;
	}
	function report() {
		pending = false;
		var msg = 'none';
		try {
			var el = deepActive(), ec = el && el.editContext;
			if (ec instanceof EC && document.hasFocus()) {
				var r = caretRect(ec);
				if (r && r.height > 0) {
					msg = Math.round(r.left) + ',' + Math.round(r.top) + ',' +
						Math.max(1, Math.round(r.width)) + ',' + Math.round(r.height);
				}
			}
		} catch (err) {}
		if (msg === last) return;
		last = msg;
		try { console.log(%(prefix)s + msg); } catch (err) {}
	}
	function schedule() {
		if (pending) return;
		pending = true;
		setTimeout(report, 0);
	}
	['updateSelectionBounds', 'updateCharacterBounds', 'updateControlBounds'].forEach(function (name) {
		var original = proto[name];
		if (typeof original !== 'function') return;
		proto[name] = function () {
			var result = original.apply(this, arguments);
			try {
				if (name === 'updateSelectionBounds') {
					var b = arguments[0];
					selection.set(this, {left: b.x, top: b.y, width: b.width, height: b.height});
				}
				schedule();
			} catch (err) {}
			return result;
		};
	});
	window.addEventListener('focusin', schedule, true);
	window.addEventListener('focusout', schedule, true);
})();"""


def _install_ime_keydown_shim(profile):
	"""给网页配置装上输入法脚本：所有标签、所有框架（含跨站框架）都注入，不按网址分流。
	一个是中转的焦点报告（+ 默认停用的 229 补发，见 WEB_IME_KEYDOWN_SHIM_JS 处说明），
	一个是“候选框位置”（只在 EditContext 编辑器里起作用，见 WEB_IME_CARET_JS 处说明）。"""
	caret = QWebEngineScript()
	caret.setName('watermelon_ime_caret')
	caret.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
	caret.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
	caret.setRunsOnSubFrames(True)
	caret.setSourceCode(WEB_IME_CARET_JS % {'prefix': json.dumps(WEB_IME_CARET_PREFIX)})
	profile.scripts().insert(caret)
	script = QWebEngineScript()
	script.setName('watermelon_ime_keydown_shim')
	script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
	script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
	script.setRunsOnSubFrames(True)
	script.setSourceCode(WEB_IME_KEYDOWN_SHIM_JS % {
		'patch229': 'true' if WEB_IME_PATCH_229 else 'false',
		'debug': 'true' if WEB_IME_DEBUG_LOG else 'false',
		'prefix': json.dumps(WEB_IME_DEBUG_PREFIX),
		'focus_prefix': json.dumps(WEB_IME_FOCUS_PREFIX),
	})
	profile.scripts().insert(script)


# ---------- 输入法中转（Word 网页版里输入法打不进字的真正修补） ----------
# 实测根因：Word 的编辑区在一个“单独进程”的内嵌框架里。QtWebEngine 会把普通按键转发给这种框架，
# 却不转发输入法的组合文字（Qt 送出的组合文字只到主页面，找不到去处，组合随即被取消，候选框闪一下就没了）。
# 用 --site-per-process 把测试框架放进单独进程即可复现；同进程的框架一切正常。
# 不关掉浏览器的站点隔离（那是安全降级），而是由 Watermelon 当中间人：焦点在这种框架里时，
# Qt 收到的输入法事件不交给网页引擎，改为在那个框架里执行脚本：已确认的文字在光标处插入一次；
# 组合中的文字（含输入法提示词）只显示在紧贴光标的悬浮框里，不写进文档。
# （曾经把组合文字写进文档再删掉：Word 会改写/重画文字，删不干净会残留，按字数兜底删还会删掉正文。
#  不写进文档就从根上不需要删除。）
# 所有网站同一个规则：打字的框在和主页面不同来源的内嵌框架里就中转（网页里看不出框架是不是单独进程，宁可多中转）。
WEB_IME_BRIDGE_APPLY_JS = r"""(function (commit, preedit) {
	var el = document.activeElement;
	var editable = function (x) { return x && (x.isContentEditable || x.tagName === 'TEXTAREA' || x.tagName === 'INPUT'); };
	if (!editable(el)) {
		var last = window.__watermelonLastEditable;   // 焦点刚被弹走：先还给最后一个编辑框
		if (last && last.isConnected) { try { last.focus(); } catch (err) {} el = last; }
	}
	if (!editable(el)) return 'no-editable-focus';
	// 1. 已确认的文字：在光标处插入一次（先发 beforeinput 让编辑器自己处理，不处理才用编辑命令）。
	//    这里从不删除任何文字——组合中的文字根本不进文档，也就不会删错正文或留下残字。
	if (commit) {
		var ok = true;
		try {
			ok = el.dispatchEvent(new InputEvent('beforeinput', {
				inputType: 'insertText', data: commit, bubbles: true, cancelable: true, composed: true
			}));
		} catch (err) { ok = true; }
		if (ok) document.execCommand('insertText', false, commit);
	}
	// 2. 组合中的文字（含输入法的提示词）：显示在紧贴光标的悬浮框里，不是文档的一部分
	var box = document.getElementById('__watermelon_ime_preview');
	if (!preedit) {
		if (box) box.style.display = 'none';
		return 'commit=' + (commit || '').length + ' preview=hidden';
	}
	if (!box) {
		box = document.createElement('div');
		box.id = '__watermelon_ime_preview';
		box.setAttribute('aria-hidden', 'true');
		box.style.cssText = 'position:fixed;z-index:2147483647;pointer-events:none;white-space:pre;'
			+ 'background:#fff;color:#000;padding:0 2px;border-radius:3px;'
			+ 'box-shadow:0 1px 4px rgba(0,0,0,.25);text-decoration:underline;text-underline-offset:3px;';
		(document.body || document.documentElement).appendChild(box);
	}
	box.textContent = preedit;
	var sel = window.getSelection();
	var rect = null;
	if (sel && sel.rangeCount) {
		var r = sel.getRangeAt(0).cloneRange();
		r.collapse(false);
		var rects = r.getClientRects();
		rect = rects.length ? rects[rects.length - 1] : r.getBoundingClientRect();
	}
	if (!rect || (!rect.left && !rect.top && !rect.height)) rect = el.getBoundingClientRect();
	var host = sel && sel.focusNode ? (sel.focusNode.nodeType === 1 ? sel.focusNode : sel.focusNode.parentElement) : el;
	try {
		var cs = getComputedStyle(host || el);
		box.style.fontSize = cs.fontSize;
		box.style.fontFamily = cs.fontFamily;
		box.style.lineHeight = rect.height ? Math.round(rect.height) + 'px' : cs.lineHeight;
	} catch (err) {}
	box.style.left = Math.round(rect.left) + 'px';
	box.style.top = Math.round(rect.top) + 'px';
	box.style.display = 'block';
	return 'commit=' + (commit || '').length + ' preview=' + preedit.length;
})(%s, %s)"""


def _normalized_frame_url(url):
	try:
		return QUrl(str(url or '')).adjusted(QUrl.UrlFormattingOption.RemoveFragment).toString()
	except Exception:
		return str(url or '')


def _find_web_frame(frame, url):
	"""在页面的框架树里按网址找内嵌框架（不含主框架）。"""
	target = _normalized_frame_url(url)
	stack = list(frame.children()) if frame is not None else []
	while stack:
		child = stack.pop(0)
		try:
			if _normalized_frame_url(child.url().toString()) == target:
				return child
			stack.extend(child.children())
		except Exception:
			continue
	return None


_IME_QUERY_NAMES = (
	'ImEnabled', 'ImCursorRectangle', 'ImFont', 'ImCursorPosition', 'ImSurroundingText', 'ImCurrentSelection',
	'ImMaximumTextLength', 'ImAnchorPosition', 'ImHints', 'ImPreferredLanguage', 'ImAbsolutePosition',
	'ImTextBeforeCursor', 'ImTextAfterCursor', 'ImEnterKeyType', 'ImAnchorRectangle', 'ImInputItemClipRectangle',
	'ImReadOnly', 'ImPlatformData',
)
_IME_QUERIES = tuple(q for q in (getattr(Qt.InputMethodQuery, n, None) for n in _IME_QUERY_NAMES) if q is not None)


def _invalidate_ime_coordinates():
	"""光标位置变了：让输入法重新来问（macOS 上 Qt 自己不会通知输入法）。"""
	try:
		QGuiApplication.inputMethod().update(Qt.InputMethodQuery.ImCursorRectangle)
	except Exception:
		pass
	if sys.platform != 'darwin':
		return
	try:
		from AppKit import NSTextInputContext
		ctx = NSTextInputContext.currentInputContext()
		if ctx is not None:
			ctx.invalidateCharacterCoordinates()
	except Exception:
		pass


class WebImeBridge(QObject):
	"""焦点在“和主页面不同来源”的内嵌框架的编辑框里时，截下 Qt 的输入法事件，直接把文字送进那个框架。
	另外：引擎不知道光标在哪（EditContext 编辑器 / 没有选区）时，替它回答输入法“光标在哪”。"""

	def __init__(self, panel):
		super().__init__(panel)
		self._panel = panel

	def _answer_caret_query(self, obj, event):
		"""输入法问光标位置（摆候选框用）。普通编辑框照引擎的答案；只有两种情况替它答：
		1) 焦点元素是 EditContext 编辑器，且编辑器报过光标位置 → 用编辑器报的；
		2) 引擎答不上来（没有光标框，候选框会落到窗口左上角）→ 用这一页上次有效的光标框。"""
		try:
			if not (event.queries() & Qt.InputMethodQuery.ImCursorRectangle):
				return False
			if not isinstance(obj, QWidget) or not self._panel.isVisible() or not self._panel.isAncestorOf(obj):
				return False
			view = self._panel.active_view()
			page = view.page() if view is not None else None
			if page is None or not hasattr(page, 'ime_caret_hint') or not view.isAncestorOf(obj):
				return False
			engine = obj.inputMethodQuery(Qt.InputMethodQuery.ImCursorRectangle)
			engine_rect = QRectF(engine) if isinstance(engine, (QRect, QRectF)) else QRectF()
			hint = page.ime_caret_hint
			if hint is not None:
				zoom = page.zoomFactor() or 1.0
				top_left = obj.mapFrom(view, QPoint(round(hint.x() * zoom), round(hint.y() * zoom)))
				rect = QRectF(top_left.x(), top_left.y(), max(1.0, hint.width() * zoom), hint.height() * zoom)
				source = 'editcontext'
			elif engine_rect.isValid():
				page.ime_last_good_rect = engine_rect
				page.note_ime_caret_source('engine')
				return False
			elif page.ime_last_good_rect is not None:
				rect = QRectF(page.ime_last_good_rect)
				source = 'last-known'
			else:
				page.note_ime_caret_source('unknown')
				return False
			page.note_ime_caret_source(source)
			queries = event.queries()
			for q in _IME_QUERIES:
				if not (queries & q):
					continue
				if q == Qt.InputMethodQuery.ImCursorRectangle:
					value = rect
				else:
					value = obj.inputMethodQuery(q)
					if q == Qt.InputMethodQuery.ImEnabled and value is None:
						value = obj.testAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
				event.setValue(q, value)
			event.accept()
			return True
		except Exception:
			return False

	def eventFilter(self, obj, event):
		if event.type() == QEvent.Type.InputMethodQuery:
			return self._answer_caret_query(obj, event)
		if event.type() != QEvent.Type.InputMethod:
			return False
		try:
			if not isinstance(obj, QWidget) or not self._panel.isVisible() or not self._panel.isAncestorOf(obj):
				return False
			view = self._panel.active_view()
			page = view.page() if view is not None else None
			frame_url = getattr(page, 'ime_bridge_frame_url', '') if page is not None else ''
			if not frame_url:
				return False
			frame = _find_web_frame(page.mainFrame(), frame_url)
			if frame is None:
				if WEB_IME_DEBUG_LOG:
					_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}bridge | frame not found, letting the engine handle it")
				return False
			commit = event.commitString() or ''
			preedit = event.preeditString() or ''
			host = QUrl(frame_url).host()

			def _report(result, host=host):
				if WEB_IME_DEBUG_LOG:
					_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}bridge | applied in {host}: {result}")

			frame.runJavaScript(WEB_IME_BRIDGE_APPLY_JS % (json.dumps(commit), json.dumps(preedit)),
								int(QWebEngineScript.ScriptWorldId.MainWorld), _report)
			event.accept()
			return True
		except Exception:
			return False


class _ImeDebugEventFilter(QObject):
	"""诊断用（只在 WEB_IME_DEBUG_LOG 打开时安装）：记录 Qt 把输入法组合文字送进网页视图的情况，只记长度不记内容。"""

	def __init__(self, panel):
		super().__init__(panel)
		self._panel = panel

	def eventFilter(self, obj, event):
		try:
			if event.type() == QEvent.Type.InputMethod and isinstance(obj, QWidget) and self._panel.isAncestorOf(obj):
				_write_ime_debug_line(
					f"{WEB_IME_DEBUG_PREFIX}qt | InputMethodEvent to {type(obj).__name__}: "
					f"composing-text length={len(event.preeditString())} committed-text length={len(event.commitString())}")
		except Exception:
			pass
		return False


def _log_qt_ime_state(where):
	"""诊断用：按键当下，Qt 认为焦点能不能接收输入法。"""
	try:
		fo = QGuiApplication.focusObject()
		if fo is None:
			_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}qt | {where}: no focus object")
			return
		q = QInputMethodQueryEvent(Qt.InputMethodQuery.ImEnabled | Qt.InputMethodQuery.ImHints)
		QApplication.sendEvent(fo, q)
		enabled = q.value(Qt.InputMethodQuery.ImEnabled)
		hints = q.value(Qt.InputMethodQuery.ImHints)
		try:
			hints = int(hints) if hints is not None else None
		except Exception:
			hints = str(hints)
		caret = 'n/a'
		try:
			raw = fo.inputMethodQuery(Qt.InputMethodQuery.ImCursorRectangle)   # 引擎自己的答案（不经过替答）
			caret = 'unknown' if not isinstance(raw, (QRect, QRectF)) or not QRectF(raw).isValid() else 'known'
		except Exception:
			pass
		_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}qt | {where}: focus={type(fo).__name__} ImEnabled={enabled} ImHints={hints} engine-caret={caret}")
	except Exception as exc:
		_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}qt | {where}: query failed {type(exc).__name__}")


def _write_ime_debug_line(message):
	"""把补发脚本的诊断输出写进数据文件夹的 ime_debug.log（只含事件类型，不含文字内容）。"""
	try:
		path = os.path.join(WATERMELON_DATA_DIR, 'ime_debug.log')
		mode = 'a'
		if os.path.exists(path) and os.path.getsize(path) > 1024 * 1024:
			mode = 'w'
		with open(path, mode, encoding='utf-8') as f0:
			f0.write(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} {message[len(WEB_IME_DEBUG_PREFIX):]}\n")
	except Exception:
		pass


# 登录页（流程网址里带一次性令牌，过期或被拒后再打开只会停在拒绝页）不记成标签页地址、也不进“最近打开”
WEB_SIGNIN_HOSTS = frozenset({
	'accounts.google.com', 'login.microsoftonline.com', 'login.microsoft.com', 'login.live.com',
})


def _web_is_signin_url(url):
	try:
		return QUrl(str(url or '')).host().lower() in WEB_SIGNIN_HOSTS
	except Exception:
		return False


def _strip_menu_icons(menu):
	try:
		for action in menu.actions():
			if not action.icon().isNull():
				action.setIcon(QIcon())
			sub = action.menu()
			if sub is not None:
				_strip_menu_icons(sub)
	except Exception:
		pass


def style_watermelon_context_menu(menu):
	"""右键 / “+” 菜单 = 系统菜单（样式书 5.3）。菜单照旧用 QMenu 写，这里给它打上记号，
	exec() 时由 glass_kit 换成系统的 NSMenu 弹出来；系统菜单用不了时退回 Qt 画的圆角菜单。"""
	return style_broccoli_context_menu(menu)


def _normalize_web_input(text):
	"""地址栏输入 → 网址：像网址的补上协议，其余当作 Google 搜索。"""
	text = str(text or '').strip()
	if not text:
		return ''
	if re.match(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://', text) or text.startswith('about:'):
		return text
	if ' ' not in text and (text.startswith('localhost') or re.match(r'^\d{1,3}(\.\d{1,3}){3}', text)):
		return 'http://' + text
	if ' ' not in text and '.' in text.strip('.'):
		return 'https://' + text
	from urllib.parse import quote_plus
	return 'https://www.google.com/search?q=' + quote_plus(text)


def _web_url_domain(url):
	try:
		from urllib.parse import urlparse
		return urlparse(url).netloc or url
	except Exception:
		return url


def _web_clean_title(title):
	title = str(title or '').strip()
	return re.sub(r'\s+[-–]\s+(Google (Docs|Slides|Sheets)|Microsoft Word|Word)$', '', title).strip()


def _web_plus_icon(dark):
	"""“+”按钮图标（Broccoli 用 plus2.png，这里直接画，资源包里不需要新图片）。"""
	size = 64
	pixmap = QPixmap(size, size)
	pixmap.fill(Qt.GlobalColor.transparent)
	painter = QPainter(pixmap)
	painter.setRenderHint(QPainter.RenderHint.Antialiasing)
	pen = QPen(QColor('#F2F2F7' if dark else '#333333'), 6)
	pen.setCapStyle(Qt.PenCapStyle.RoundCap)
	painter.setPen(pen)
	painter.drawLine(32, 14, 32, 50)
	painter.drawLine(14, 32, 50, 32)
	painter.end()
	return QIcon(pixmap)


def _web_icon_pixmap():
	"""Web 按钮图标：地球（画法同提词器图标，对齐 speaker.png 的线条风格）。"""
	size = 500
	pixmap = QPixmap(size, size)
	pixmap.fill(Qt.GlobalColor.transparent)
	painter = QPainter(pixmap)
	painter.setRenderHint(QPainter.RenderHint.Antialiasing)
	pen = QPen(QColor(255, 255, 255, 216), 44)
	pen.setCapStyle(Qt.PenCapStyle.RoundCap)
	pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
	painter.setPen(pen)
	painter.setBrush(Qt.BrushStyle.NoBrush)
	painter.drawEllipse(QRectF(48, 48, 404, 404))   # 外圈
	painter.drawEllipse(QRectF(166, 48, 168, 404))  # 经线
	painter.drawLine(60, 250, 440, 250)             # 赤道
	painter.end()
	return pixmap


def _pill_lerp_rect(r1, r2, t):
	def li(a, b):
		return int(round(a + (b - a) * t))
	return QRect(li(r1.x(), r2.x()), li(r1.y(), r2.y()),
				 li(r1.width(), r2.width()), li(r1.height(), r2.height()))


class WebSitePill(QWidget):
	"""
	一个标签页（移植自 Broccoli NavSitePill）。
	- 激活态：长条 pill，显示 favicon + 标题；非激活态：圆形，只显示 favicon/首字母。
	- 双击激活态：就地编辑网址；右键：后退/前进/左移/右移/主页/刷新/关闭。
	"""
	clicked_sig = pyqtSignal()
	delete_requested = pyqtSignal()
	refresh_requested = pyqtSignal()
	back_requested = pyqtSignal()
	forward_requested = pyqtSignal()
	home_requested = pyqtSignal()
	move_left_requested = pyqtSignal()
	move_right_requested = pyqtSignal()
	url_submitted = pyqtSignal(str)
	hover_entered = pyqtSignal()
	hover_left = pyqtSignal()

	CIRCLE_SIZE = 34
	HEIGHT = 34

	def __init__(self, url='', label='', active=False, edit_on_show=False, parent=None):
		super().__init__(parent)
		self._url = url
		self._label = label or (self._domain(url) if url else '')
		self._icon = None
		self._active = active
		self._edit_on_show = edit_on_show
		w = 190 if active else self.CIRCLE_SIZE
		self._cur_w = w
		self.setFixedSize(w, self.HEIGHT)
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self._timer = QTimer(self)
		self._timer.setInterval(14)
		self._timer.timeout.connect(self._tick)
		self._t0 = w
		self._t1 = w
		self._prog = 1.0
		self._x0 = 0
		self._x1 = 0
		self._y = 0
		self._has_pos = False
		self._le = QLineEdit(self)
		self._le.setVisible(False)
		self._apply_theme()
		self._le.returnPressed.connect(self._submit)
		self._le.installEventFilter(self)

	def _apply_theme(self):
		dark = is_dark_theme(app)
		self._le.setStyleSheet(
			f"QLineEdit {{ border: none; background: transparent;"
			f" color: {'#F2F2F7' if dark else '#222222'}; font-size: 12px; padding: 0; }}"
		)

	@staticmethod
	def _domain(url):
		return _web_url_domain(url)

	def showEvent(self, event):
		super().showEvent(event)
		if self._edit_on_show:
			self._edit_on_show = False
			QTimer.singleShot(50, self.enter_edit_mode)
		if getattr(self, '_broccoli_inwindow_glass', None) is None:
			# 只有缩成圆的标签是自己的玻璃圆片；展开的那个（带标题）和就地编辑框照旧画进标签栏的玻璃里
			install_inwindow_circle_glass(
				self, lambda w: QRect((w.CIRCLE_SIZE - 26) // 2, (w.HEIGHT - 26) // 2, 26, 26),
				wanted_for=lambda w: not w._active and not w._le.isVisible() and w._cur_w <= w.CIRCLE_SIZE + 2,
				dark_for=lambda w: is_dark_theme(app))

	def set_icon(self, pixmap):
		self._icon = pixmap
		self.update()

	def set_label(self, text):
		self._label = self._domain(text) if '://' in text else text
		self.update()

	def set_target_geometry(self, x, y, target_w, animated=False):
		x = int(x)
		y = int(y)
		target_w = max(self.CIRCLE_SIZE, int(target_w or self.CIRCLE_SIZE))
		self._y = y
		if not animated or not self._has_pos:
			first_layout = not self._has_pos
			self._has_pos = True
			self._x0 = self._x1 = x
			self.move(x, y)
			if animated and first_layout and self._cur_w != target_w:
				self._t0 = self._cur_w
				self._t1 = target_w
				self._prog = 0.0
				self._timer.start()
				return
			self._timer.stop()
			self._prog = 1.0
			self._cur_w = target_w
			self._t0 = self._t1 = target_w
			self.setFixedWidth(target_w)
			if self._le.isVisible():
				self._le.setGeometry(self.CIRCLE_SIZE + 4, 2, self._cur_w - self.CIRCLE_SIZE - 8, self.HEIGHT - 4)
			parent = self.parentWidget()
			if parent is not None:
				parent.update()
			return
		if self._timer.isActive() and self._x1 == x and self._t1 == target_w:
			return
		if not self._timer.isActive() and self._cur_w == target_w and self.x() == x and self.y() == y:
			return
		self._x0 = self.x()
		self._t0 = self._cur_w
		self._x1 = x
		self._t1 = target_w
		self._prog = 0.0
		self._timer.start()

	def _tick(self):
		self._prog = min(1.0, self._prog + 0.08)
		t = 1.0 - (1.0 - self._prog) ** 3
		self._cur_w = int(self._t0 + (self._t1 - self._t0) * t)
		self.setFixedWidth(max(self.CIRCLE_SIZE, self._cur_w))
		if self._has_pos and self._x0 != self._x1:
			self.move(int(round(self._x0 + (self._x1 - self._x0) * t)), self._y)
		if self._le.isVisible():
			edit_w = max(0, self._cur_w - self.CIRCLE_SIZE - 8)
			self._le.setGeometry(self.CIRCLE_SIZE + 4, 2, edit_w, self.HEIGHT - 4)
		p = self.parentWidget()
		if p:
			p.update()
		if self._prog >= 1.0:
			self._timer.stop()

	def enter_edit_mode(self):
		if not self._active:
			return
		self._le.setText(self._url)
		edit_w = max(0, self._cur_w - self.CIRCLE_SIZE - 8)
		self._le.setGeometry(self.CIRCLE_SIZE + 4, 2, edit_w, self.HEIGHT - 4)
		self._le.setVisible(True)
		self._le.selectAll()
		self._le.setFocus()
		self.update()

	def _submit(self):
		url = _normalize_web_input(self._le.text())
		self._le.setVisible(False)
		if url:
			self._url = url
			self._label = self._domain(url)
			self.update()
			self.url_submitted.emit(url)

	def eventFilter(self, obj, event):
		if obj is self._le and event.type() == QEvent.Type.KeyPress:
			if event.key() == Qt.Key.Key_Escape:
				self._le.setVisible(False)
				if not self._url:
					self.delete_requested.emit()
				return True
		return super().eventFilter(obj, event)

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.clicked_sig.emit()

	def mouseDoubleClickEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton and self._active:
			self.enter_edit_mode()

	def enterEvent(self, event):
		self.hover_entered.emit()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.hover_left.emit()
		super().leaveEvent(event)

	def contextMenuEvent(self, event):
		menu = style_watermelon_context_menu(QMenu(self))
		back_act = menu.addAction(_tr('← Back'))
		fwd_act = menu.addAction(_tr('→ Forward'))
		menu.addSeparator()
		move_left_act = menu.addAction(_tr('Move Left'))
		move_right_act = menu.addAction(_tr('Move Right'))
		menu.addSeparator()
		home_act = menu.addAction(_tr('Home'))
		ref_act = menu.addAction(_tr('Refresh'))
		menu.addSeparator()
		del_act = menu.addAction(_tr('Close Tab'))
		act = menu.exec(event.globalPos())
		if act == back_act:
			self.back_requested.emit()
		elif act == fwd_act:
			self.forward_requested.emit()
		elif act == move_left_act:
			self.move_left_requested.emit()
		elif act == move_right_act:
			self.move_right_requested.emit()
		elif act == home_act:
			self.home_requested.emit()
		elif act == ref_act:
			self.refresh_requested.emit()
		elif act == del_act:
			self.delete_requested.emit()

	def paintEvent(self, event):
		if self._le.isVisible():
			return
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		dark = is_dark_theme(app)
		bar = self.parentWidget()
		expanded_by_bar = False
		if bar is not None and hasattr(bar, '_expanded_index') and hasattr(bar, '_pills'):
			try:
				expanded_by_bar = 0 <= bar._expanded_index < len(bar._pills) and bar._pills[bar._expanded_index] is self
			except Exception:
				expanded_by_bar = False
		expanded = self._active or expanded_by_bar
		icon_size = 20
		icon_y = (self.HEIGHT - icon_size) // 2
		bg_size = 26
		bg_x = (self.CIRCLE_SIZE - bg_size) / 2.0
		bg_y = (self.HEIGHT - bg_size) / 2.0
		if not getattr(self, '_liquid_glass_active', False):   # 有玻璃时图标后面的圆片就是玻璃
			painter.setBrush(QBrush(QColor('#3A3A3A' if dark else '#FFFFFF')))
			painter.setPen(Qt.PenStyle.NoPen)
			painter.drawEllipse(QRectF(bg_x, bg_y, bg_size, bg_size))
		if self._icon and not self._icon.isNull():
			icon_x = (self.CIRCLE_SIZE - icon_size) // 2
			clip = QPainterPath()
			clip.addEllipse(icon_x, icon_y, icon_size, icon_size)
			painter.setClipPath(clip)
			painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
			painter.drawPixmap(QRect(icon_x, icon_y, icon_size, icon_size), self._icon)
			painter.setClipping(False)
		else:
			painter.setPen(QPen(QColor('#D0D0D4' if dark else '#555555')))
			f = painter.font()
			f.setPixelSize(13)
			f.setBold(True)
			painter.setFont(f)
			painter.drawText(QRect(0, 0, self.CIRCLE_SIZE, self.HEIGHT), Qt.AlignmentFlag.AlignCenter,
							 self._label[0].upper() if self._label else '+')
		if expanded and self._cur_w > self.CIRCLE_SIZE + 20:
			fade_range = max(1, self._cur_w - self.CIRCLE_SIZE - 20)
			alpha = min(255, int(fade_range / 60 * 255))
			tc = QColor('#F2F2F7' if dark else '#333333')
			tc.setAlpha(alpha)
			painter.setPen(QPen(tc))
			f2 = painter.font()
			f2.setPixelSize(12)
			f2.setBold(False)
			painter.setFont(f2)
			text_x = self.CIRCLE_SIZE + 4
			text_w = max(0, self._cur_w - text_x - 6)
			if text_w > 0:
				elided = painter.fontMetrics().elidedText(self._label, Qt.TextElideMode.ElideMiddle, text_w)
				painter.drawText(QRect(text_x, 0, text_w, self.HEIGHT),
								 Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)
		painter.end()


# 页面加载后在 <head> 里找分辨率最高的图标链接
_ICON_JS = (
	"(function(){"
	"  var found = [];"
	"  document.querySelectorAll('link[rel]').forEach(function(l){"
	"    var rel = (l.getAttribute('rel')||'').toLowerCase();"
	"    if (!rel.includes('icon')) return;"
	"    var href = l.href;"
	"    if (!href || href === window.location.href) return;"
	"    var isTouch = rel.includes('apple-touch-icon');"
	"    var sz = isTouch ? 180 : 0;"
	"    var s = l.getAttribute('sizes');"
	"    if (s) { var p = s.split('x'); var n = parseInt(p[0])||0; if (n > sz) sz = n; }"
	"    found.push([sz, href]);"
	"  });"
	"  found.sort(function(a,b){ return b[0]-a[0]; });"
	"  return found.length ? found[0][1] : '';"
	"})()"
)


class _IconFetcher(QObject):
	"""后台线程下载 favicon，把字节交回主线程（同 Broccoli）。"""
	icon_ready = pyqtSignal(object, bytes)   # (view, image_bytes)

	def fetch(self, view, url):
		threading.Thread(target=self._download, args=(view, url), daemon=True).start()

	def _download(self, view, url):
		try:
			import urllib.request
			req = urllib.request.Request(url, headers={'User-Agent': (
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
				'AppleWebKit/537.36 (KHTML, like Gecko) '
				'Chrome/120.0.0.0 Safari/537.36'
			)})
			with urllib.request.urlopen(req, timeout=6) as resp:
				data = resp.read(512 * 1024)
			if data:
				self.icon_ready.emit(view, data)
		except Exception:
			pass


class WatermelonWebPage(QWebEnginePage):
	"""网页：允许页面读写剪贴板；新窗口/弹窗交给面板开成新标签页。"""

	def __init__(self, profile, parent):
		super().__init__(profile, parent)
		self.new_window_handler = None
		self.ime_bridge_frame_url = ''   # 可编辑焦点所在的不同来源内嵌框架（输入法中转用）
		self._ime_bridge_clear_timer = QTimer(self)
		self._ime_bridge_clear_timer.setSingleShot(True)
		self._ime_bridge_clear_timer.setInterval(300)   # 焦点离开 0.3 秒内没回来才停止中转
		self._ime_bridge_clear_timer.timeout.connect(self._clear_ime_bridge)
		self.urlChanged.connect(lambda _url: self._clear_ime_bridge())
		self.ime_caret_hint = None        # EditContext 编辑器报的光标框（主页面网页坐标），见 WEB_IME_CARET_JS
		self.ime_last_good_rect = None    # 引擎上次答出的有效光标框（网页视图坐标）
		self._ime_caret_source = ''
		self.urlChanged.connect(lambda _url: self._clear_ime_caret())
		try:
			settings = self.settings()
			for attr_name in ('JavascriptCanAccessClipboard', 'JavascriptCanPaste'):
				attr = getattr(QWebEngineSettings.WebAttribute, attr_name, None)
				if attr is not None:
					settings.setAttribute(attr, True)
		except Exception:
			pass
		self.newWindowRequested.connect(self._on_new_window)
		try:
			self.featurePermissionRequested.connect(self._on_feature_permission_requested)
		except Exception:
			pass

	def _on_feature_permission_requested(self, security_origin, feature):
		try:
			clipboard_feature = getattr(QWebEnginePage.Feature, 'ClipboardReadWrite', None)
			if clipboard_feature is not None and feature == clipboard_feature:
				self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
		except Exception:
			pass

	def javaScriptConsoleMessage(self, level, message, line_number, source_id):
		text = str(message or '')
		if text.startswith(WEB_IME_CARET_PREFIX):
			self._on_ime_caret_report(text[len(WEB_IME_CARET_PREFIX):].strip())
			return
		if text.startswith(WEB_IME_FOCUS_PREFIX):
			state, _, href = text[len(WEB_IME_FOCUS_PREFIX):].partition(' ')
			changed = False
			if state == 'in':
				self._ime_bridge_clear_timer.stop()
				changed = _normalized_frame_url(href) != _normalized_frame_url(self.ime_bridge_frame_url)
				self.ime_bridge_frame_url = href
			elif state == 'out' and _normalized_frame_url(href) == _normalized_frame_url(self.ime_bridge_frame_url):
				self._ime_bridge_clear_timer.start()
				changed = True
			elif state == 'top' and self.ime_bridge_frame_url:
				self._clear_ime_bridge()
				changed = True
			if WEB_IME_DEBUG_LOG and changed:
				_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}bridge | editable focus {state} {QUrl(href).host()}")
			return
		if WEB_IME_DEBUG_LOG and text.startswith(WEB_IME_DEBUG_PREFIX):
			_write_ime_debug_line(text)
			return
		super().javaScriptConsoleMessage(level, message, line_number, source_id)

	def _clear_ime_bridge(self):
		self._ime_bridge_clear_timer.stop()
		self.ime_bridge_frame_url = ''

	def _on_ime_caret_report(self, payload):
		hint = None
		if payload != 'none':
			try:
				x, y, w, h = (float(v) for v in payload.split(','))
				if h > 0:
					hint = QRectF(x, y, max(1.0, w), h)
			except Exception:
				hint = None
		if hint == self.ime_caret_hint:
			return
		was_set = self.ime_caret_hint is not None
		self.ime_caret_hint = hint
		if WEB_IME_DEBUG_LOG and (hint is None) == was_set:
			_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}caret | EditContext editor {'reports its caret' if hint is not None else 'lost focus'}")
		view = QWebEngineView.forPage(self)
		focus = QApplication.focusWidget()
		if view is not None and focus is not None and (focus is view or view.isAncestorOf(focus)):
			_invalidate_ime_coordinates()

	def _clear_ime_caret(self):
		self.ime_caret_hint = None
		self.ime_last_good_rect = None

	def note_ime_caret_source(self, source):
		"""诊断用：记下输入法问光标位置时用的是谁的答案（只在变化时写一行）。"""
		if source == self._ime_caret_source:
			return
		self._ime_caret_source = source
		if WEB_IME_DEBUG_LOG:
			_write_ime_debug_line(f"{WEB_IME_DEBUG_PREFIX}caret | IME asked where the caret is -> {source}")

	def _on_new_window(self, request):
		# 必须在这个信号里同步处理（openIn），请求对象离开信号就失效
		handler = self.new_window_handler
		if callable(handler):
			try:
				handler(self, request)
				return
			except Exception:
				logging.exception('web new window failed')
		url = request.requestedUrl()
		if url.isValid() and url.scheme() in ('http', 'https'):
			view = QWebEngineView.forPage(self)   # Qt 6 的网页对象没有 view()
			if view is not None:
				QTimer.singleShot(0, lambda: view.load(url))


class WebTabBar(QWidget):
	"""
	网页区底部的标签栏（移植自 Broccoli WebNavBar）。
	- 圆角 bar；激活标签是长条 pill，其余是圆形图标；"+" 贴右侧。
	- "+"：有历史时弹出历史菜单 + New Tab，没有历史直接开新标签页（开始页）。
	"""
	view_selected = pyqtSignal(int)
	site_submitted = pyqtSignal(int, str)
	site_deleted = pyqtSignal(int)
	site_reset_requested = pyqtSignal(int)
	site_refresh_requested = pyqtSignal(int)
	site_back_requested = pyqtSignal(int)
	site_forward_requested = pyqtSignal(int)
	site_home_requested = pyqtSignal(int)
	site_move_requested = pyqtSignal(int, int)
	saved_url_selected = pyqtSignal(str, str)
	new_tab_requested = pyqtSignal()

	def __init__(self, sites, active=0, parent=None):
		super().__init__(parent)
		self._theme_updating = False
		self._history_provider = None
		self._sites = list(sites)
		self._active = max(0, min(int(active or 0), max(0, len(self._sites) - 1)))
		self._hovered = -1
		self._pills = []
		self._bar_bg = QColor('#FFFFFF')
		self._active_bg = QColor('#DEDEDE')
		self._layout_margin = 3
		self._layout_spacing = 4
		self._min_expanded_width = 190
		self._expanded_index = self._active
		self._scroll_offset = 0
		self._max_scroll_offset = 0
		self._content_width = 0
		self._ensure_active_on_next_layout = True
		self._hl_rect = QRect()
		self._hl_start = QRect()
		self._hl_end = QRect()
		self._hl_prog = 1.0
		self._hl_timer = QTimer(self)
		self._hl_timer.setInterval(14)
		self._hl_timer.timeout.connect(self._hl_tick)
		self._setup_ui()

	def _setup_ui(self):
		self.setFixedHeight(40)
		shadow = QGraphicsDropShadowEffect(self)
		shadow.setBlurRadius(40)
		shadow.setXOffset(0)
		shadow.setYOffset(0)
		shadow.setColor(QColor(0, 0, 0, 40))
		self.setGraphicsEffect(shadow)
		for i, site in enumerate(self._sites):
			pill = WebSitePill(url=site.get('url', ''), label=site.get('label', ''), active=(i == self._active), parent=self)
			self._connect_pill(pill)
			self._pills.append(pill)
		self._plus_btn = QPushButton('', self)
		self._plus_btn.setFixedSize(34, 34)
		self._plus_btn.setIconSize(QSize(16, 16))
		self._plus_btn.setToolTip(_tr('New Tab'))
		self._plus_btn.clicked.connect(self._on_add)
		self._apply_theme()
		QTimer.singleShot(0, self._relayout_static)
		QTimer.singleShot(80, self._relayout_static)

	def _relayout_static(self):
		self._relayout_pills(animated=False)

	def _hl_tick(self):
		self._hl_prog = min(1.0, self._hl_prog + 0.08)
		t = 1.0 - (1.0 - self._hl_prog) ** 3
		self._hl_rect = _pill_lerp_rect(self._hl_start, self._hl_end, t)
		self.update()
		if self._hl_prog >= 1.0:
			self._hl_timer.stop()

	def _set_highlight_target(self, rect, animated):
		rect = QRect(rect) if rect is not None else QRect()
		if not rect.isValid():
			self._hl_timer.stop()
			self._hl_rect = QRect()
			self._hl_start = QRect()
			self._hl_end = QRect()
			self._hl_prog = 1.0
			self.update()
			return
		if not animated or not self._hl_rect.isValid():
			self._hl_timer.stop()
			self._hl_rect = QRect(rect)
			self._hl_start = QRect(rect)
			self._hl_end = QRect(rect)
			self._hl_prog = 1.0
			self.update()
			return
		if self._hl_timer.isActive() and self._hl_end == rect:
			return
		if not self._hl_timer.isActive() and self._hl_rect == rect:
			self._hl_end = QRect(rect)
			return
		self._hl_start = QRect(self._hl_rect)
		self._hl_end = QRect(rect)
		self._hl_prog = 0.0
		self._hl_timer.start()

	def _relayout_pills(self, animated=False):
		if not hasattr(self, '_plus_btn'):
			return
		margin = self._layout_margin
		spacing = self._layout_spacing
		circle = WebSitePill.CIRCLE_SIZE
		y = max(0, (self.height() - circle) // 2)
		plus_x = max(margin, self.width() - margin - self._plus_btn.width())
		self._plus_btn.setGeometry(plus_x, y, self._plus_btn.width(), self._plus_btn.height())
		url_left = margin
		url_right = max(url_left, plus_x - spacing)
		available = max(0, url_right - url_left)
		count = len(self._pills)
		if count <= 0:
			self._set_highlight_target(QRect(), False)
			self._plus_btn.raise_()
			self.update()
			return
		expanded_index = self._active if 0 <= self._active < count else -1
		self._expanded_index = expanded_index
		min_expanded_w = min(max(circle, int(self._min_expanded_width)), max(circle, available))
		widths = [circle for _ in self._pills]
		if expanded_index >= 0:
			left_reserved = (circle + spacing) if expanded_index > 0 else 0
			right_reserved = (circle + spacing) if expanded_index < count - 1 else 0
			widths[expanded_index] = min(min_expanded_w, max(circle, available - left_reserved - right_reserved))
		logical_positions = []
		x = 0
		for index, width in enumerate(widths):
			logical_positions.append(x)
			x += width + (spacing if index < count - 1 else 0)
		self._content_width = max(0, x)
		self._max_scroll_offset = max(0, self._content_width - available)
		self._scroll_offset = max(0, min(int(self._scroll_offset), self._max_scroll_offset))
		if self._ensure_active_on_next_layout and 0 <= expanded_index < count:
			item_left = logical_positions[expanded_index]
			item_right = item_left + widths[expanded_index]
			if item_left < self._scroll_offset:
				self._scroll_offset = item_left
			elif item_right > self._scroll_offset + available:
				self._scroll_offset = item_right - available
			self._scroll_offset = max(0, min(int(self._scroll_offset), self._max_scroll_offset))
			self._ensure_active_on_next_layout = False
		positions = []
		active_x = None
		active_w = widths[expanded_index] if 0 <= expanded_index < count else circle
		if 0 <= expanded_index < count:
			raw_active_x = url_left + logical_positions[expanded_index] - self._scroll_offset
			min_active_x = url_left + ((circle + spacing) if expanded_index > 0 else 0)
			max_active_x = url_right - active_w - ((circle + spacing) if expanded_index < count - 1 else 0)
			if max_active_x < min_active_x:
				min_active_x = url_left
				max_active_x = max(url_left, url_right - active_w)
			active_x = int(round(max(min_active_x, min(max_active_x, raw_active_x))))
		left_edge_stack = []
		active_left_stack = []
		active_right_stack = []
		right_edge_stack = []
		for index, width in enumerate(widths):
			raw_x = url_left + logical_positions[index] - self._scroll_offset
			if index == expanded_index and active_x is not None:
				positions.append(active_x)
				continue
			if active_x is not None and index < expanded_index:
				left_slot = max(url_left, active_x - spacing - circle)
				if raw_x + width > active_x - spacing:
					active_left_stack.append(index)
					positions.append(left_slot)
				elif raw_x < url_left:
					left_edge_stack.append(index)
					positions.append(url_left)
				else:
					positions.append(int(round(max(url_left, min(max(url_left, active_x - spacing - width), raw_x)))))
				continue
			if active_x is not None and index > expanded_index:
				right_slot = min(max(url_left, url_right - width), active_x + active_w + spacing)
				if raw_x < active_x + active_w + spacing:
					active_right_stack.append(index)
					positions.append(right_slot)
				elif raw_x + width > url_right:
					right_edge_stack.append(index)
					positions.append(max(url_left, url_right - width))
				else:
					positions.append(int(round(max(active_x + active_w + spacing, min(max(url_left, url_right - width), raw_x)))))
				continue
			positions.append(int(round(max(url_left, min(max(url_left, url_right - width), raw_x)))))
		if active_x is not None:
			active_left_slot = max(url_left, active_x - spacing - circle)
			active_right_slot = min(max(url_left, url_right - circle), active_x + active_w + spacing)
		else:
			active_left_slot = url_left
			active_right_slot = max(url_left, url_right - circle)
		for index in left_edge_stack:
			positions[index] = url_left
		for index in active_left_stack:
			positions[index] = active_left_slot
		for index in active_right_stack:
			positions[index] = active_right_slot
		for index in right_edge_stack:
			positions[index] = max(url_left, url_right - circle)
		for index, pill in enumerate(self._pills):
			pill._active = (index == self._active)
			pill.set_target_geometry(int(positions[index]), y, max(circle, int(widths[index])), animated=animated)
			pill.show()
		hl_index = self._expanded_index if 0 <= self._expanded_index < count else self._active
		if 0 <= hl_index < count:
			self._set_highlight_target(
				QRect(int(positions[hl_index]), y, max(circle, int(widths[hl_index])), WebSitePill.HEIGHT), animated)
		else:
			self._set_highlight_target(QRect(), False)
		if self._content_width > available and 0 <= expanded_index < count:
			for index in left_edge_stack + active_left_stack + list(reversed(right_edge_stack)) + active_right_stack:
				self._pills[index].raise_()
			for index in range(count):
				if (index not in left_edge_stack and index not in active_left_stack
						and index not in active_right_stack and index not in right_edge_stack
						and index != expanded_index):
					self._pills[index].raise_()
			self._pills[expanded_index].raise_()
		else:
			for pill in self._pills:
				pill.raise_()
			if 0 <= self._active < count:
				self._pills[self._active].raise_()
		self._plus_btn.raise_()
		self.update()

	def wheelEvent(self, event):
		delta = 0
		try:
			pixel = event.pixelDelta()
			angle = event.angleDelta()
			if not pixel.isNull() and pixel.x():
				delta = pixel.x()
			elif angle.x():
				delta = int(angle.x() / 3)
			elif event.modifiers() & Qt.KeyboardModifier.ShiftModifier and angle.y():
				delta = int(angle.y() / 3)
		except Exception:
			delta = 0
		if not delta or self._max_scroll_offset <= 0:
			super().wheelEvent(event)
			return
		self._ensure_active_on_next_layout = False
		self._scroll_offset = max(0, min(self._max_scroll_offset, int(self._scroll_offset - delta)))
		self._relayout_pills(animated=False)
		event.accept()

	def showEvent(self, event):
		super().showEvent(event)
		QTimer.singleShot(0, self._relayout_static)
		QTimer.singleShot(80, self._relayout_static)
		if getattr(self, '_broccoli_inwindow_glass', None) is None and inwindow_glass_available():
			QTimer.singleShot(120, self._attach_liquid_glass)

	# 液态玻璃：整条标签栏是一颗玻璃胶囊，高亮滑块和标签画进玻璃里（同 Broccoli 的 WebNavBar）
	def _attach_liquid_glass(self):
		try:
			if getattr(self, '_broccoli_inwindow_glass', None) is None and self.isVisible():
				attach_inwindow_liquid_glass(self, lambda w=self: w.height() / 2.0,
											 lambda w=self: w._bar_bg.lightness() < 128)
		except RuntimeError:
			pass

	def _on_inwindow_glass_changed(self, active):
		effect = self.graphicsEffect()
		if effect is not None:
			effect.setEnabled(not active)   # 玻璃自己带阴影

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._ensure_active_on_next_layout = True
		self._relayout_pills(animated=False)

	def _apply_theme(self):
		if self._theme_updating:
			return
		self._theme_updating = True
		try:
			dark = is_dark_theme(app)
			if dark:
				self._bar_bg = QColor('#2D2D2D')
				self._active_bg = QColor('#3A3A3A')
				self._plus_btn.setStyleSheet("""
					QPushButton { background-color: rgba(255,255,255,0.10); border: none; border-radius: 17px; }
					QPushButton:hover { background-color: rgba(255,255,255,0.16); }
					QPushButton:pressed { background-color: rgba(255,255,255,0.22); }
				""")
			else:
				self._bar_bg = QColor('#FFFFFF')
				self._active_bg = QColor('#DEDEDE')
				self._plus_btn.setStyleSheet("""
					QPushButton { background-color: rgba(0,0,0,0.06); border: none; border-radius: 17px; }
					QPushButton:hover { background-color: rgba(0,0,0,0.10); }
					QPushButton:pressed { background-color: rgba(0,0,0,0.15); }
				""")
			self._plus_btn.setIcon(_web_plus_icon(dark))
			for pill in self._pills:
				pill._apply_theme()
				pill.update()
			self.update()
		finally:
			self._theme_updating = False

	def changeEvent(self, event):
		super().changeEvent(event)
		if self._theme_updating:
			return
		if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
			self._apply_theme()

	def _connect_pill(self, pill):
		pill.installEventFilter(self)
		pill.clicked_sig.connect(lambda p=pill: self._select_pill(p))
		pill.delete_requested.connect(lambda p=pill: self._delete_pill(p))
		pill.refresh_requested.connect(lambda p=pill: self.site_refresh_requested.emit(self._pills.index(p)))
		pill.back_requested.connect(lambda p=pill: self.site_back_requested.emit(self._pills.index(p)))
		pill.forward_requested.connect(lambda p=pill: self.site_forward_requested.emit(self._pills.index(p)))
		pill.home_requested.connect(lambda p=pill: self.site_home_requested.emit(self._pills.index(p)))
		pill.move_left_requested.connect(lambda p=pill: self._move_pill(p, -1))
		pill.move_right_requested.connect(lambda p=pill: self._move_pill(p, 1))
		pill.url_submitted.connect(lambda url, p=pill: self.site_submitted.emit(self._pills.index(p), url))

	def eventFilter(self, obj, event):
		if event.type() == QEvent.Type.Wheel and obj in self._pills:
			self.wheelEvent(event)
			return event.isAccepted()
		return super().eventFilter(obj, event)

	def _move_pill(self, pill, delta):
		if pill not in self._pills:
			return
		old_idx = self._pills.index(pill)
		new_idx = old_idx + int(delta)
		if not (0 <= new_idx < len(self._pills)):
			return
		self._pills.pop(old_idx)
		self._pills.insert(new_idx, pill)
		if self._active == old_idx:
			self._active = new_idx
		elif old_idx < self._active <= new_idx:
			self._active -= 1
		elif new_idx <= self._active < old_idx:
			self._active += 1
		for index, item in enumerate(self._pills):
			item._active = (index == self._active)
		self._ensure_active_on_next_layout = True
		self._relayout_pills(animated=True)
		self.site_move_requested.emit(old_idx, new_idx)

	def _select_pill(self, pill):
		idx = self._pills.index(pill)
		if idx == self._active:
			self._relayout_pills(animated=True)
			return
		if 0 <= self._active < len(self._pills):
			self._pills[self._active]._active = False
			self._pills[self._active]._le.setVisible(False)
		self._active = idx
		self._pills[idx]._active = True
		self._ensure_active_on_next_layout = True
		self._relayout_pills(animated=True)
		self.view_selected.emit(idx)

	def _select(self, idx):
		if 0 <= idx < len(self._pills):
			self._select_pill(self._pills[idx])

	def set_history_provider(self, provider):
		"""provider() -> [{'url': str, 'label': str}]"""
		self._history_provider = provider

	def _on_add(self):
		entries = []
		if callable(self._history_provider):
			try:
				entries = [e for e in list(self._history_provider() or [])
						   if isinstance(e, dict) and str(e.get('url', '') or '').strip()]
			except Exception:
				entries = []
		if not entries:
			self.new_tab_requested.emit()
			return
		menu = style_watermelon_context_menu(QMenu(self))
		menu.setToolTipsVisible(True)
		new_action = menu.addAction(_tr('New Tab'))
		menu.addSeparator()
		actions = []
		for entry in entries[:15]:
			url = str(entry.get('url', '') or '').strip()
			label = str(entry.get('label', '') or '').strip()
			action = menu.addAction(label or (url if len(url) <= 64 else url[:61] + '…'))
			action.setToolTip(url)
			actions.append((action, url, label))
		# 系统菜单从这个点往下摆：按系统菜单的行高（24，上下各 5）算出它的高，让它落在 "+" 的上方
		menu_height = 10 + 24 * (1 + len(actions)) + 11
		chosen = menu.exec(self._plus_btn.mapToGlobal(QPoint(0, -menu_height - 6)))
		if chosen is new_action:
			self.new_tab_requested.emit()
			return
		for action, url, label in actions:
			if chosen is action:
				self.saved_url_selected.emit(url, label)
				return

	def _delete_pill(self, pill):
		if pill not in self._pills:
			return
		idx = self._pills.index(pill)
		if len(self._pills) <= 1:
			# 最后一个标签不真正删除，原地恢复成 New Tab（开始页）
			pill._url = ''
			pill._label = WEB_TAB_BLANK_LABEL
			pill._le.setVisible(False)
			pill._active = True
			pill.set_icon(None)
			self._active = idx
			self._ensure_active_on_next_layout = True
			self._relayout_pills(animated=True)
			self.site_reset_requested.emit(idx)
			self.update()
			return
		pill.deleteLater()
		self._pills.pop(idx)
		if idx < self._active or self._active >= len(self._pills):
			self._active = max(0, self._active - 1)
		for index, item in enumerate(self._pills):
			item._active = (index == self._active)
		self._ensure_active_on_next_layout = True
		self._relayout_pills(animated=True)
		self.site_deleted.emit(idx)
		self.view_selected.emit(self._active)
		self.update()

	def delete_index(self, idx):
		if 0 <= idx < len(self._pills):
			self._delete_pill(self._pills[idx])

	def set_pill_site(self, idx, url, label=''):
		if not (0 <= idx < len(self._pills)):
			return
		pill = self._pills[idx]
		pill._url = str(url or '')
		pill._label = str(label or '') or WebSitePill._domain(url)
		pill.update()

	def set_pill_icon(self, idx, pixmap):
		if 0 <= idx < len(self._pills):
			self._pills[idx].set_icon(pixmap)

	def add_pill(self, url, label=''):
		if 0 <= self._active < len(self._pills):
			self._pills[self._active]._active = False
			self._pills[self._active]._le.setVisible(False)
		pill = WebSitePill(url=url, label=label or WebSitePill._domain(url), active=True, parent=self)
		self._connect_pill(pill)
		self._pills.append(pill)
		self._active = len(self._pills) - 1
		pill.show()
		self._ensure_active_on_next_layout = True
		self._relayout_pills(animated=True)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		r = self.height() / 2.0
		painter.setPen(Qt.PenStyle.NoPen)
		if not getattr(self, '_liquid_glass_active', False):   # 有玻璃时标签栏本身就是玻璃
			painter.setBrush(QBrush(self._bar_bg))
			painter.drawRoundedRect(0, 0, self.width(), self.height(), r, r)
		if self._hl_rect.isValid() and self._hl_end.isValid() and self._hl_end.width() > WebSitePill.CIRCLE_SIZE:
			pr = self._hl_rect.height() / 2.0
			painter.setBrush(QBrush(self._active_bg))
			painter.drawRoundedRect(self._hl_rect, pr, pr)
		painter.end()


def web_start_page_html(dark, recent):
	"""开始页：搜索/地址框 + 常用在线文档 + 最近打开。"""
	bg = '#2D2D2D' if dark else '#FFFFFF'
	fg = '#F2F2F7' if dark else '#20242B'
	muted = '#A7AEB8' if dark else '#6A717C'
	card = '#3A3A3A' if dark else '#F4F4F6'
	card_hover = '#454545' if dark else '#EAEAEE'
	border = '#4A4A4A' if dark else '#DADADF'
	esc = html_lib.escape
	tiles = ''.join(
		f'<a class="tile" href="{esc(url)}"><span class="badge" style="background:{color}">{esc(name[0])}</span>'
		f'<span class="name">{esc(name)}</span></a>'
		for name, url, color in WEB_START_SHORTCUTS
	)
	recent_rows = ''
	for entry in list(recent or [])[:8]:
		url = str(entry.get('url', '') or '').strip()
		if not url.startswith('http'):
			continue
		label = str(entry.get('label', '') or '').strip() or _web_url_domain(url)
		recent_rows += (f'<a class="row" href="{esc(url)}"><span class="rl">{esc(label)}</span>'
						f'<span class="rh">{esc(_web_url_domain(url))}</span></a>')
	recent_block = f'<div class="section">{html_lib.escape(_tr("Recent"))}</div>{recent_rows}' if recent_rows else ''
	return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{WEB_TAB_BLANK_LABEL}</title>
<style>
	html, body {{ margin: 0; height: 100%; background: {bg}; color: {fg};
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
	body {{ display: flex; justify-content: center; }}
	.shell {{ width: 560px; max-width: 90%; padding-top: 14vh; }}
	h1 {{ margin: 0 0 22px 0; font-size: 30px; font-weight: 700; letter-spacing: -0.03em; text-align: center; }}
	form {{ margin: 0 0 26px 0; }}
	input {{ width: 100%; box-sizing: border-box; padding: 12px 16px; font-size: 15px; border-radius: 12px;
		border: 1px solid {border}; background: {card}; color: {fg}; outline: none; }}
	input:focus {{ border-color: #0A84FF; }}
	.tiles {{ display: flex; gap: 12px; margin-bottom: 30px; }}
	.tile {{ flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 18px 8px;
		border-radius: 14px; background: {card}; color: {fg}; text-decoration: none; font-size: 13px; }}
	.tile:hover {{ background: {card_hover}; }}
	.badge {{ width: 40px; height: 40px; border-radius: 10px; color: #fff; font-weight: 700; font-size: 19px;
		display: flex; align-items: center; justify-content: center; }}
	.section {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: {muted}; margin: 0 0 8px 4px; }}
	.row {{ display: flex; justify-content: space-between; gap: 16px; padding: 9px 12px; border-radius: 10px;
		color: {fg}; text-decoration: none; font-size: 14px; }}
	.row:hover {{ background: {card}; }}
	.rl {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
	.rh {{ color: {muted}; font-size: 12px; white-space: nowrap; }}
</style></head>
<body><div class="shell">
	<h1>Watermelon Web</h1>
	<form onsubmit="go(); return false;"><input id="q" placeholder="{html_lib.escape(_tr('Search Google or enter an address'), quote=True)}" autocomplete="off"></form>
	<div class="tiles">{tiles}</div>
	{recent_block}
</div>
<script>
function go() {{
	var t = document.getElementById('q').value.trim();
	if (!t) return;
	var url;
	if (/^[a-zA-Z][a-zA-Z0-9+.\\-]*:\\/\\//.test(t)) url = t;
	else if (t.indexOf(' ') < 0 && /^(localhost|\\d{{1,3}}(\\.\\d{{1,3}}){{3}})/.test(t)) url = 'http://' + t;
	else if (t.indexOf(' ') < 0 && t.replace(/^\\.+|\\.+$/g, '').indexOf('.') >= 0) url = 'https://' + t;
	else url = 'https://www.google.com/search?q=' + encodeURIComponent(t).replace(/%20/g, '+');
	location.href = url;
}}
</script>
</body></html>"""


_WEB_ZERO_WIDTH_RE = re.compile('[' + ''.join(map(chr, (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF))) + ']')


def _web_clean_text(text):
	"""去掉零宽字符、把不换行空格变普通空格、行中间连续的空格并成一个（代码块不动）、收掉多余空行。"""
	text = _WEB_ZERO_WIDTH_RE.sub('', str(text or '')).replace('\xa0', ' ')
	lines, in_code = [], False
	for line in text.split('\n'):
		if line.lstrip().startswith('```'):
			in_code = not in_code
		elif not in_code and not line.startswith(('    ', '\t')):
			line = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', line)
		lines.append(line)
	return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()


def _web_clipboard_to_markdown(html, text):
	"""复制得到的内容 → Markdown：有 HTML 就转（保留标题、列表、粗体、斜体、链接），否则用纯文字。
	只按通用的网页写法整理，不认网站：粗细/斜体写在 style 里的也认，标着“不加粗”的 <b> 不当粗体
	（例：从 Google 文档复制时整段外面包着 <b style="font-weight:normal">）。"""
	md = ''
	if html and html.strip():
		try:
			soup = BeautifulSoup(html, 'html.parser')
			for tag in soup(['script', 'style', 'meta', 'title', 'head']):
				tag.decompose()
			for tag in soup.find_all(True):
				style = str(tag.get('style') or '').replace(' ', '').lower()
				if tag.name in ('b', 'strong') and re.search(r'font-weight:(normal|[1-5]00)\b', style):
					tag.name = 'span'
				elif tag.name == 'span':
					bold = re.search(r'font-weight:(bold|[6-9]00)\b', style)
					italic = 'font-style:italic' in style
					if bold:
						tag.name = 'b'
					if italic:
						if bold:
							inner = soup.new_tag('i')
							for child in list(tag.contents):
								inner.append(child.extract())
							tag.append(inner)
						else:
							tag.name = 'i'
			html = str(soup)
		except Exception:
			pass
		md = _web_html_to_markdown(html)
	if not md.strip():
		md = text or ''
	return _web_clean_text(md)


class WebCopyCapture(QObject):
	"""“存到本地 / Notes”取内容。所有网页同一个做法，和手动复制一样：
	1) 让网页执行“复制”，拿到选中的内容；
	2) 什么都没选中 → 先按一次“全选”（⌘A，由网页自己处理，和手按一样）再复制；
	   复制完按一下左方向键收起这次全选，免得接着打字把全文替换掉；
	3) 剪贴板原来的内容事后原样放回去。
	复制由网页自己完成，所以内容在单独进程的内嵌框架里（如 Word 网页版）、或画在画布上（如 Google 文档）也一样拿得到。"""
	SELECTION_WAIT_MS = 900     # 等“复制选中内容”的结果；等不到就当没选中
	SELECT_ALL_WAIT_MS = 3000   # 全选后复制，大文档要久一点

	def __init__(self, view, done, parent):
		super().__init__(parent)
		self._view = view
		self._done = done   # done(markdown, error)
		self._clipboard = QApplication.clipboard()
		self._saved = None
		self._marker = ''
		self._phase = ''
		self._finished = False
		self._timer = QTimer(self)
		self._timer.setSingleShot(True)
		self._timer.timeout.connect(self._on_timeout)

	def start(self):
		self._saved = self._snapshot_clipboard()
		self._clipboard.dataChanged.connect(self._on_clipboard_changed)
		self._view.setFocus()
		self._phase = 'selection'
		self._copy(self.SELECTION_WAIT_MS)

	def _snapshot_clipboard(self):
		snap = QMimeData()
		try:
			src = self._clipboard.mimeData()
			if src is not None:
				for fmt in src.formats():
					snap.setData(fmt, src.data(fmt))
		except Exception:
			pass
		return snap

	def _copy(self, wait_ms):
		# 先放一个记号，复制没有产生新内容（没选中）时就能看出来
		self._marker = f'watermelon-copy-{time.time_ns()}'
		self._clipboard.setText(self._marker)
		self._view.page().triggerAction(QWebEnginePage.WebAction.Copy)
		self._timer.start(wait_ms)

	def _on_clipboard_changed(self):
		if self._finished:
			return
		mime = self._clipboard.mimeData()
		if mime is None:
			return
		text = mime.text() if mime.hasText() else ''
		if text == self._marker:
			return
		md = _web_clipboard_to_markdown(mime.html() if mime.hasHtml() else '', text)
		if md:
			self._finish(md, '')

	def _on_timeout(self):
		if self._finished:
			return
		if self._phase == 'selection':
			self._phase = 'select_all'
			self._press(Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)   # Qt 在 macOS 上把 ⌘ 叫 Control
			QTimer.singleShot(150, self._copy_after_select_all)
		else:
			self._finish('', _tr('Nothing to save'))

	def _copy_after_select_all(self):
		if not self._finished:
			self._copy(self.SELECT_ALL_WAIT_MS)

	def _press(self, key, modifiers=Qt.KeyboardModifier.NoModifier):
		target = self._view.focusProxy() or self._view
		for event_type in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
			QApplication.sendEvent(target, QKeyEvent(event_type, key, modifiers, ''))

	def _finish(self, md, error):
		if self._finished:
			return
		self._finished = True
		self._timer.stop()
		try:
			self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
		except Exception:
			pass
		if self._phase == 'select_all':
			self._press(Qt.Key.Key_Left)   # 收起自己做的全选
		try:
			if self._saved is not None and self._saved.formats():
				self._clipboard.setMimeData(self._saved)
			else:
				self._clipboard.clear()
		except Exception:
			pass
		self._saved = None
		self.deleteLater()
		self._done(md, error)


def _web_html_to_markdown(html):
	try:
		converter = html2text.HTML2Text()
		converter.body_width = 0
		return converter.handle(html or '').strip()
	except Exception:
		return ''


def _web_text_looks_like_html(text):
	head = str(text or '')[:600].lower()
	return '<!doctype html' in head or '<html' in head


class WebModePanel(QWidget):
	"""网页区：一摞 QWebEngineView（每个标签一个）+ 底部标签栏。"""
	active_url_changed = pyqtSignal(str)
	active_selection_changed = pyqtSignal(str)
	active_nav_state_changed = pyqtSignal(bool, bool)
	focus_address_requested = pyqtSignal()
	toast_requested = pyqtSignal(str)

	CAPTURE_TIMEOUT_MS = 25000

	def __init__(self, profile, state_dir, parent=None):
		super().__init__(parent)
		self.setObjectName('WebModePanel')
		self._profile = profile
		self._sites_path = os.path.join(state_dir, 'web_tabs.json')
		self._history_path = os.path.join(state_dir, 'web_tabs_history.json')
		self._url_history = self._load_url_history()
		self._sites, self._active_idx = self._load_sites()
		self._views = []
		self._captures = {}
		self._copy_capture = None   # 正在进行的“存到本地 / Notes”取内容（WebCopyCapture）
		self._icon_fetcher = _IconFetcher()
		self._icon_fetcher.icon_ready.connect(self._on_hq_icon, Qt.ConnectionType.QueuedConnection)
		self._icon_size = {}
		self._save_timer = QTimer(self)
		self._save_timer.setSingleShot(True)
		self._save_timer.setInterval(600)
		self._save_timer.timeout.connect(self.save_now)
		self._start_page_dark = None
		self._setup()

	# ── 持久化 ────────────────────────────────────────────
	def _load_sites(self):
		try:
			with open(self._sites_path, 'r', encoding='utf-8') as f0:
				data = json.load(f0)
			tabs = [
				{'url': str(t.get('url', '') or '').strip(), 'label': str(t.get('label', '') or '').strip()}
				for t in data.get('tabs', []) if isinstance(t, dict)
			]
			for tab in tabs:
				if _web_is_signin_url(tab['url']):
					# 旧版本存下的登录/拒绝页：恢复成开始页，免得一打开就停在 Google 的拒绝页上
					tab['url'] = ''
					tab['label'] = WEB_TAB_BLANK_LABEL
			if tabs:
				active = int(data.get('active', 0) or 0)
				return tabs, max(0, min(active, len(tabs) - 1))
		except Exception:
			pass
		return [{'url': '', 'label': WEB_TAB_BLANK_LABEL}], 0

	def save_now(self):
		self._save_timer.stop()
		try:
			payload = {'tabs': [{'url': s.get('url', ''), 'label': s.get('label', '')} for s in self._sites],
					   'active': int(self._active_idx)}
			tmp_path = self._sites_path + '.tmp'
			with open(tmp_path, 'w', encoding='utf-8') as f0:
				json.dump(payload, f0, ensure_ascii=False, indent=2)
			os.replace(tmp_path, self._sites_path)
		except Exception:
			pass

	def _schedule_save(self):
		self._save_timer.start()

	def _load_url_history(self):
		try:
			with open(self._history_path, 'r', encoding='utf-8') as f0:
				loaded = json.load(f0)
			return [
				{'url': str(e.get('url', '') or '').strip(), 'label': str(e.get('label', '') or '').strip()}
				for e in loaded if isinstance(e, dict) and str(e.get('url', '') or '').strip()
			]
		except Exception:
			return []

	def _save_url_history(self):
		try:
			with open(self._history_path, 'w', encoding='utf-8') as f0:
				json.dump(self._url_history, f0, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def _record_url_history(self, url, label=''):
		"""最近打开：同一网址只留一条并挪到最前，最多 30 条。"""
		url = str(url or '').strip()
		if not url.startswith('http') or _web_is_signin_url(url):
			return
		label = str(label or '').strip() or _web_url_domain(url)
		self._url_history = [e for e in self._url_history if e.get('url') != url]
		self._url_history.insert(0, {'url': url, 'label': label})
		del self._url_history[30:]
		self._save_url_history()

	def url_history_entries(self):
		return [dict(e) for e in self._url_history]

	# ── 界面 ──────────────────────────────────────────────
	def _setup(self):
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		self._frame = QFrame(self)
		self._frame.setObjectName('webModeFrame')
		frame_layout = QVBoxLayout(self._frame)
		frame_layout.setContentsMargins(1, 1, 1, 1)
		frame_layout.setSpacing(0)
		self._stack = QStackedWidget(self._frame)
		frame_layout.addWidget(self._stack)
		layout.addWidget(self._frame, 1)
		for site in self._sites:
			view = self._make_view()
			self._views.append(view)
			self._stack.addWidget(view)
			if site.get('url'):
				view.setProperty('wm_pending_url', site['url'])   # 切到它时才真正加载
				host = QUrl(site['url']).host()
				if host:
					self._icon_fetcher.fetch(view, f'https://www.google.com/s2/favicons?domain={host}&sz=128')
			else:
				self._show_start_page(view)
		self._nav = WebTabBar(self._sites, active=self._active_idx, parent=self)
		self._nav.set_history_provider(self.url_history_entries)
		self._nav.view_selected.connect(self._switch)
		self._nav.site_submitted.connect(self._on_site_submitted)
		self._nav.site_deleted.connect(self._on_site_deleted)
		self._nav.site_reset_requested.connect(self._on_site_reset)
		self._nav.site_refresh_requested.connect(lambda i: self._view_call(i, 'reload'))
		self._nav.site_back_requested.connect(lambda i: self._view_call(i, 'back'))
		self._nav.site_forward_requested.connect(lambda i: self._view_call(i, 'forward'))
		self._nav.site_home_requested.connect(self._on_site_home)
		self._nav.site_move_requested.connect(self._on_site_moved)
		self._nav.saved_url_selected.connect(self.open_saved_url)
		self._nav.new_tab_requested.connect(self.new_blank_tab)
		nav_wrap = QWidget(self)
		nav_wrap.setObjectName('webNavWrap')
		nav_layout = QHBoxLayout(nav_wrap)
		nav_layout.setContentsMargins(10, 10, 10, 10)
		nav_layout.setSpacing(0)
		nav_layout.addWidget(self._nav, 1)
		layout.addWidget(nav_wrap)
		self._apply_theme()
		self._stack.setCurrentIndex(self._active_idx)

	def _apply_theme(self):
		dark = is_dark_theme(app)
		if dark == self._start_page_dark:
			return   # 只在明暗真的变了时重设（setStyleSheet 本身也会触发 PaletteChange，否则会无限递归）
		previous = self._start_page_dark
		self._start_page_dark = dark
		bg = '#2D2D2D' if dark else '#FFFFFF'
		border = '#555555' if dark else 'grey'
		self.setStyleSheet(
			f'QWidget#WebModePanel, QWidget#webNavWrap {{ background: transparent; border: none; }}'
			f'QFrame#webModeFrame {{ border: 1px solid {border}; border-radius: 4px; background: {bg}; }}'
		)
		if previous is not None:
			for view in self._views:
				if bool(view.property('wm_start_page')):
					self._show_start_page(view)

	def changeEvent(self, event):
		super().changeEvent(event)
		if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
			self._apply_theme()

	def _make_view(self):
		view = QWebEngineView()
		use_native_web_context_menu(view)   # 网页自己的右键菜单（后退、复制…）也用系统菜单
		page = WatermelonWebPage(self._profile, view)
		page.new_window_handler = self._on_page_new_window
		view.setPage(page)
		page.windowCloseRequested.connect(lambda v=view: self._close_view(v))
		page.selectionChanged.connect(lambda v=view: self._on_selection(v))
		view.iconChanged.connect(lambda icon, v=view: self._on_icon(v, icon))
		view.urlChanged.connect(lambda url, v=view: self._on_url(v, url))
		view.titleChanged.connect(lambda title, v=view: self._on_title(v, title))
		view.loadFinished.connect(lambda ok, v=view: self._on_load(v, ok))
		return view

	def _show_start_page(self, view):
		view.setProperty('wm_start_page', True)
		view.setHtml(web_start_page_html(is_dark_theme(app), self._url_history), QUrl('about:blank'))

	def _view_index(self, view):
		try:
			return self._views.index(view)
		except ValueError:
			return -1

	def _view_call(self, idx, method):
		if 0 <= idx < len(self._views):
			try:
				getattr(self._views[idx], method)()
			except Exception:
				pass

	def _load_into(self, idx, url):
		if not (0 <= idx < len(self._views)) or not url:
			return
		view = self._views[idx]
		view.setProperty('wm_pending_url', None)
		view.setProperty('wm_start_page', False)
		view.load(QUrl(url))

	def _ensure_loaded(self, idx):
		if 0 <= idx < len(self._views):
			pending = self._views[idx].property('wm_pending_url')
			if pending:
				self._load_into(idx, pending)

	def active_view(self):
		if not self._views:
			return None
		self._active_idx = max(0, min(self._active_idx, len(self._views) - 1))
		return self._views[self._active_idx]

	def activate(self):
		"""进入网页模式时调用：加载当前标签（若还没加载）并同步地址栏等状态。"""
		self._ensure_loaded(self._active_idx)
		self._emit_active_state()

	def _emit_active_state(self):
		view = self.active_view()
		if view is None:
			return
		url_text = view.url().toString()
		if bool(view.property('wm_start_page')) or not url_text.startswith('http'):
			url_text = str(view.property('wm_pending_url') or '')
		self.active_url_changed.emit(url_text)
		history = view.history()
		self.active_nav_state_changed.emit(bool(history.canGoBack()), bool(history.canGoForward()))
		self.active_selection_changed.emit(view.page().selectedText() or '')

	def _switch(self, idx):
		if not (0 <= idx < len(self._views)):
			return
		self._active_idx = idx
		self._stack.setCurrentIndex(idx)
		self._ensure_loaded(idx)
		self._emit_active_state()
		self._schedule_save()

	# ── 标签操作 ──────────────────────────────────────────
	def _append_tab(self, url='', label=''):
		self._sites.append({'url': url, 'label': label or (_web_url_domain(url) if url else WEB_TAB_BLANK_LABEL)})
		view = self._make_view()
		self._views.append(view)
		self._stack.addWidget(view)
		self._nav.add_pill(url, self._sites[-1]['label'])
		self._active_idx = len(self._views) - 1
		self._stack.setCurrentIndex(self._active_idx)
		self._schedule_save()
		return view

	def _blank_tab_index(self):
		for idx, view in enumerate(self._views):
			if bool(view.property('wm_start_page')) and not self._sites[idx].get('url'):
				return idx
		return -1

	def new_blank_tab(self):
		idx = self._blank_tab_index()
		if idx >= 0:
			self._nav._select(idx)
			if idx == self._active_idx:
				self._emit_active_state()
		else:
			view = self._append_tab('', WEB_TAB_BLANK_LABEL)
			self._show_start_page(view)
			self._emit_active_state()
		self.focus_address_requested.emit()

	def open_saved_url(self, url, label=''):
		url = _normalize_web_input(url)
		if not url:
			return
		for idx, site in enumerate(self._sites):
			if site.get('url') == url:
				self._nav._select(idx)
				return
		idx = self._blank_tab_index()
		if idx >= 0:
			self._nav._select(idx)
			self._load_into(idx, url)
			return
		self._append_tab(url, label)
		self._load_into(self._active_idx, url)
		self._emit_active_state()

	def navigate_active(self, text):
		url = _normalize_web_input(text)
		if url:
			self._load_into(self._active_idx, url)

	def go_back(self):
		self._view_call(self._active_idx, 'back')

	def go_forward(self):
		self._view_call(self._active_idx, 'forward')

	def reload_active(self):
		view = self.active_view()
		if view is None:
			return
		if bool(view.property('wm_start_page')):
			self._show_start_page(view)
		else:
			view.reload()

	def _on_page_new_window(self, page, request):
		# 新窗口/弹窗 → 新标签页；openIn 让弹窗保留 window.opener（登录弹窗要靠它回传结果）
		url = request.requestedUrl().toString()
		view = self._append_tab(url if url.startswith('http') else '', '')
		request.openIn(view.page())
		self._emit_active_state()

	def _close_view(self, view):
		idx = self._view_index(view)
		if idx >= 0:
			self._nav.delete_index(idx)

	def _on_site_deleted(self, idx):
		if 0 <= idx < len(self._sites):
			self._sites.pop(idx)
		if 0 <= idx < len(self._views):
			view = self._views.pop(idx)
			self._icon_size.pop(view, None)
			self._stack.removeWidget(view)
			view.deleteLater()
		self._active_idx = max(0, min(self._nav._active, len(self._views) - 1))
		self._schedule_save()

	def _on_site_reset(self, idx):
		if not (0 <= idx < len(self._views)):
			return
		self._sites[idx] = {'url': '', 'label': WEB_TAB_BLANK_LABEL}
		view = self._views[idx]
		view.stop()
		view.setProperty('wm_pending_url', None)
		self._show_start_page(view)
		self._active_idx = idx
		self._stack.setCurrentIndex(idx)
		self._emit_active_state()
		self._schedule_save()

	def _on_site_submitted(self, idx, url):
		self._load_into(idx, url)

	def _on_site_home(self, idx):
		if 0 <= idx < len(self._views):
			url = QUrl(self._views[idx].url())
			if url.scheme() in ('http', 'https') and url.host():
				self._load_into(idx, f'{url.scheme()}://{url.host()}/')

	def _on_site_moved(self, old_idx, new_idx):
		if not (0 <= old_idx < len(self._views) and 0 <= new_idx < len(self._views)) or old_idx == new_idx:
			return
		self._sites.insert(new_idx, self._sites.pop(old_idx))
		view = self._views.pop(old_idx)
		self._views.insert(new_idx, view)
		self._stack.removeWidget(view)
		self._stack.insertWidget(new_idx, view)
		self._active_idx = self._nav._active
		self._stack.setCurrentIndex(self._active_idx)
		self._schedule_save()

	# ── view 信号 ─────────────────────────────────────────
	def _on_url(self, view, url):
		idx = self._view_index(view)
		if idx < 0:
			return
		url_text = url.toString()
		if url_text.startswith('http'):
			view.setProperty('wm_start_page', False)
			if not _web_is_signin_url(url_text):
				self._sites[idx]['url'] = url_text     # 记住当前所在网址，重启后回到这里（登录页除外）
				if not self._sites[idx].get('label') or self._sites[idx]['label'] == WEB_TAB_BLANK_LABEL:
					self._sites[idx]['label'] = _web_url_domain(url_text)
				self._schedule_save()
			self._nav.set_pill_site(idx, url_text, self._sites[idx].get('label') or _web_url_domain(url_text))
			self._icon_size.pop(view, None)
		if idx == self._active_idx:
			self._emit_active_state()

	def _on_title(self, view, title):
		idx = self._view_index(view)
		if idx < 0 or bool(view.property('wm_start_page')):
			return
		url_text = view.url().toString()
		if not url_text.startswith('http'):
			return
		label = str(title or '').strip()
		if not label or label == url_text or label.startswith('http'):
			label = _web_url_domain(url_text)
		self._nav.set_pill_site(idx, url_text, label)
		if not _web_is_signin_url(url_text):
			self._sites[idx]['label'] = label
			self._schedule_save()

	def _on_load(self, view, ok):
		idx = self._view_index(view)
		if idx < 0:
			return
		url_text = view.url().toString()
		if ok and url_text.startswith('http'):
			self._record_url_history(url_text, self._sites[idx].get('label', ''))
			try:
				view.page().runJavaScript(_ICON_JS, lambda icon_url, v=view: icon_url and self._icon_fetcher.fetch(v, icon_url))
			except Exception:
				pass
			host = view.url().host()
			if host:
				self._icon_fetcher.fetch(view, f'https://www.google.com/s2/favicons?domain={host}&sz=128')
		if idx == self._active_idx:
			self._emit_active_state()

	def _on_icon(self, view, icon):
		idx = self._view_index(view)
		if idx < 0:
			return
		sizes = icon.availableSizes()
		pix = icon.pixmap(max(sizes, key=lambda s: s.width() * s.height())) if sizes else icon.pixmap(QSize(128, 128))
		if not pix.isNull() and max(pix.width(), pix.height()) >= self._icon_size.get(view, 0):
			self._icon_size[view] = max(pix.width(), pix.height())
			self._nav.set_pill_icon(idx, pix)

	def _on_hq_icon(self, view, data):
		idx = self._view_index(view)
		if idx < 0:
			return
		pix = QPixmap()
		pix.loadFromData(data)
		if not pix.isNull() and max(pix.width(), pix.height()) >= self._icon_size.get(view, 0):
			self._icon_size[view] = max(pix.width(), pix.height())
			self._nav.set_pill_icon(idx, pix)

	def _on_selection(self, view):
		if self._view_index(view) == self._active_idx:
			self.active_selection_changed.emit(view.page().selectedText() or '')

	def has_typing_focus(self):
		focus = QApplication.focusWidget()
		return focus is not None and self._stack.isAncestorOf(focus)

	# ── 下载 ──────────────────────────────────────────────
	def handle_download(self, download):
		"""Qt 不会自动下载：这里不 accept 的下载会被直接取消。"""
		try:
			name = os.path.basename(str(download.downloadFileName() or '').strip())
			token = next((t for t in self._captures if name.startswith(t)), None) if name.startswith(WEB_CAPTURE_PREFIX) else None
			if token is not None:
				download.setDownloadDirectory(self._captures[token]['dir'])
				# 中断的下载不算 finished（还能续传），所以两个信号都要听，否则失败时要干等到超时
				download.isFinishedChanged.connect(lambda d=download, t=token: self._on_capture_finished(t, d))
				download.stateChanged.connect(lambda _state, d=download, t=token: self._on_capture_finished(t, d))
				download.accept()
				return
			base_dir = os.path.join(str(Path.home()), 'Downloads')
			if not os.path.isdir(base_dir):
				base_dir = str(Path.home())
			chosen, _filter = QFileDialog.getSaveFileName(self, _tr('Save Download'), os.path.join(base_dir, name or 'download'))
			if not chosen:
				download.cancel()
				return
			download.setDownloadDirectory(os.path.dirname(chosen) or base_dir)
			download.setDownloadFileName(os.path.basename(chosen) or name or 'download')
			download.isFinishedChanged.connect(lambda d=download: self._on_user_download_finished(d))
			download.stateChanged.connect(lambda _state, d=download: self._on_user_download_finished(d))
			download.accept()
		except Exception:
			logging.exception('web download failed')
			try:
				download.cancel()
			except Exception:
				pass

	def _on_user_download_finished(self, download):
		state = download.state()
		if state not in (QWebEngineDownloadRequest.DownloadState.DownloadCompleted,
						 QWebEngineDownloadRequest.DownloadState.DownloadInterrupted):
			return
		if download.property('wm_reported'):
			return   # 两个信号都会到，只提示一次
		download.setProperty('wm_reported', True)
		if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
			self.toast_requested.emit(_tr('Downloaded: %1').replace('%1', download.downloadFileName()))
		else:
			self.toast_requested.emit(_tr('Download failed'))

	def _capture_export(self, url, callback):
		"""用浏览器自己的下载（带登录 cookie）把导出文件抓到临时目录，读出文字后回调 callback(text or None)。"""
		view = self.active_view()
		if view is None:
			callback(None)
			return
		self._capture_seq = getattr(self, '_capture_seq', 0) + 1
		token = f'{WEB_CAPTURE_PREFIX}{int(time.time() * 1000)}_{self._capture_seq}'
		self._captures[token] = {'dir': tempfile.mkdtemp(prefix='watermelon_web_'), 'callback': callback, 'done': False}
		timeout_timer = QTimer(self)
		timeout_timer.setSingleShot(True)
		timeout_timer.timeout.connect(lambda t=token: self._finish_capture(t, None))
		timeout_timer.timeout.connect(timeout_timer.deleteLater)
		timeout_timer.start(self.CAPTURE_TIMEOUT_MS)
		view.page().download(QUrl(url), token + '.txt')

	def _on_capture_finished(self, name, download):
		state = download.state()
		if state not in (QWebEngineDownloadRequest.DownloadState.DownloadCompleted,
						 QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
						 QWebEngineDownloadRequest.DownloadState.DownloadCancelled):
			return   # 还在下载
		text = None
		if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
			path = os.path.join(download.downloadDirectory(), download.downloadFileName())
			try:
				with open(path, 'r', encoding='utf-8', errors='replace') as f0:
					text = f0.read()
			except Exception:
				text = None
			try:
				os.remove(path)
			except Exception:
				pass
		self._finish_capture(name, text)

	def _finish_capture(self, name, text):
		capture = self._captures.get(name)
		if capture is None or capture['done']:
			return
		capture['done'] = True
		self._captures.pop(name, None)
		try:
			os.rmdir(capture['dir'])
		except Exception:
			pass
		if text is not None and (_web_text_looks_like_html(text) or not text.strip()):
			text = None   # 没登录/没权限时拿到的是网页，不是导出文件
		capture['callback'](text)

	# ── “存到本地 / Notes”：取出当前页面内容（Markdown）──────────
	def extract_active_markdown(self, callback):
		"""callback(title, markdown, error)。所有网页同一个做法（见 WebCopyCapture）：存选中的内容，没选中就先全选。"""
		view = self.active_view()
		if view is None or bool(view.property('wm_start_page')):
			callback('', '', _tr('Open a page first'))
			return
		title = _web_clean_title(view.page().title()) or _web_url_domain(view.url().toString()) or 'Web Clip'
		if self._copy_capture is not None:
			callback(title, '', _tr('Still saving, one moment'))
			return

		def done(md, error):
			self._copy_capture = None
			callback(title, md, '' if md else (error or _tr('Nothing to save')))

		self._copy_capture = WebCopyCapture(view, done, self)
		self._copy_capture.start()


class NoteCreateWorker(QThread):
	"""在后台新建一条 Apple Notes 笔记（osascript）。"""
	result = pyqtSignal(bool, str)

	def __init__(self, creator, folder, title, html, parent=None):
		super().__init__(parent)
		self.creator = creator
		self.folder = folder
		self.title = title
		self.html = html

	def run(self):
		try:
			folder = self.creator(self.folder, self.title, self.html)
			self.result.emit(True, folder or self.folder or 'Notes')
		except Exception as exc:
			self.result.emit(False, str(exc))


def default_font_family():
	"""The font behind "Default font" (lastused.txt = '0'): the system's own font for the interface language.
	2026-11-26 (Ryan: "要不要把默认字体换掉，好，换。"): it used to be the bundled chillduanheisong_widelight.otf,
	a font with one weight only: the bold-reading view could not show its bold in running text (only tables,
	which use another font, did). The system fonts have a real bold."""
	wanted = {'zh': ('PingFang SC', 'Heiti SC'), 'ja': ('Hiragino Sans', 'Hiragino Kaku Gothic ProN')}.get(
		str(UI_LANGUAGE or '')[:2], ())
	try:
		families = set(QFontDatabase.families())
	except Exception:
		families = set()
	for name in tuple(wanted) + ('Helvetica Neue', 'Helvetica'):
		if name in families:
			return name
	return 'Helvetica Neue'


class window3(QWidget):  # 主窗口
	broccoli_send_done = pyqtSignal(bool, str)   # 后台线程发完给 Broccoli 以后
	broccoli_write_done = pyqtSignal(bool, str, str)   # 「在此处续写」交给 Broccoli 以后：成功？说明、请求编号

	def __init__(self):
		super().__init__()
		self._splitter2_ratio = None
		self._splitter2_user_set = False
		self._always_on_top = True
		self._screen_signals_connected = False
		self._tracked_screen = None
		self._current_bg_color = '#FFFFFF'  # 默认白色背景
		self._teleprompter_mode = False
		self.sound_mode_enabled = False
		self._sound_bell_played = False
		self._hit_mask_ready = False
		self._notes_focus_check_worker = None
		self.web_mode_enabled = False
		self.web_panel = None
		self.office_panel = None   # Office 文件的编辑面板，第一次打开 Office 文件时才创建
		self._notes_drawing_confirmed = set()   # 已经确认过“画的图会变成图片”的笔记
		self._notes_open_note = None        # 正开着的那张笔记（字典：folder / title / id）
		self._notes_base_md = ''            # 它上次和备忘录对齐时的 Markdown（三方合并的“原来的样子”）
		self._notes_base_fp = ''            # 那时备忘录存储的指纹
		self._notes_save_worker = None
		self._notes_save_state = ''         # '' / 'saving' / 'saved' / 'failed'
		self._notes_autosave_off = set()    # 这次运行里不自动存的笔记（用户不同意把画的图等变成普通内容）
		self._notes_conflict_snoozed = ''   # 冲突时点了 Cancel 的那份文字：文字没再变就不再问
		self._web_profile = None
		self._web_selected_text = ''
		self._note_create_workers = []
		self.initUI()

	def initUI(self):
		self._always_on_top = self._load_always_on_top()
		self._apply_window_flags()
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
		SCREEN_HEIGHT = int(self.screen().availableGeometry().height())
		self.resize(1520, SCREEN_HEIGHT)
		self.i = 1
		self.notes_loader = None
		self.notes_cache_worker = None
		self.notes_cache_path = NOTES_CACHE_PATH
		self.notes_data = []
		self.notes_current_list = []
		self.notes_folder_dialog = None
		self.notes_current_folder = None
		self.notes_current_title = None
		self.notes_active = False
		self.notes_dirty = False
		self.notes_reload_pending = False
		self.notes_mode_enabled = False
		self.notes_force_reload = False
		self.notes_pending_title = None
		self.notes_pending_folder = None
		self.notes_require_match_on_show = False
		self.notes_awaiting_reselect = False  # 防止重复弹窗的标志
		self.notes_last_folder = None
		self.notes_last_title = None
		self.notes_refresh_in_progress = False
		self._notes_positions = {}
		self.notes_wait_dialog = None
		self.notes_wait_timer = None
		self.notes_wait_target = None
		self.notes_wait_start = None
		self.mode_backup_timer = None
		self._mode_backup_lock = threading.Lock()
		self._last_local_backup_meta = {}
		self._last_notes_backup_hash = {}
		self.local_mode_backup_root = ""
		self.notes_mode_backup_root = ""
		self._preview_render_worker = None
		self._preview_render_pending_text = None
		self._preview_render_pending_token = 0
		self._preview_render_request_token = 0
		self._preview_render_timer = QTimer(self)
		self._preview_render_timer.setSingleShot(True)
		self._preview_render_timer.timeout.connect(self._start_preview_render_worker)
		self.notes_cache_worker = NotesCacheWorker(self.notes_cache_path, self)
		self.notes_cache_worker.start()
		self._setup_notes_sync()

		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		self.local_mode_backup_root = os.path.join(fulldir1, "Local Mode")
		self.notes_mode_backup_root = os.path.join(fulldir1, "Notes Mode")
		os.makedirs(self.local_mode_backup_root, exist_ok=True)
		os.makedirs(self.notes_mode_backup_root, exist_ok=True)
		self.apply_backup_limit_now(load_mode_backup_limit())

		self._current_font_size = self._read_font_size()
		self._current_font_family = self._resolve_font_family()
		self.set_textedit_font(self._current_font_size, self._current_font_family)

		self.topleft = QWebEngineView(self)
		init_bg = '#3A3A3A' if is_dark_theme(app) else '#FFFFFF'
		self.topleft.setStyleSheet(f"border: 0px; background: {init_bg};")
		self.topleft.page().setBackgroundColor(QColor(init_bg))
		self.topleft_frame = QFrame(self)
		self.topleft_frame.setObjectName("webFrame")
		self.topleft_frame.setMaximumHeight(SCREEN_HEIGHT - 200)
		topleft_layout = QVBoxLayout(self.topleft_frame)
		topleft_layout.setContentsMargins(1, 5, 1, 3)
		topleft_layout.setSpacing(0)
		topleft_layout.addWidget(self.topleft)
		self.topleft.setMaximumHeight(SCREEN_HEIGHT - 200)
		self.topleftshow = 1

		self.topright = QTextEdit(self)
		self.topright.setMaximumHeight(SCREEN_HEIGHT - 200)
		self.topright.setReadOnly(True)
		#self.topright.setDisabled(True)
		self.toprightshow = 1

		self.bottom = QTextEdit(self)
		self.bottom.setFixedWidth(1235)
		self.bottom.setAcceptRichText(False)
		self.bottom.textChanged.connect(self.text_change)
		self.bottom.textChanged.connect(self._update_word_count_label)
		self.scrollbar = self.bottom.verticalScrollBar()
		self.scrollbar.valueChanged.connect(self.scrollchanged)
		self.bottom.cursorPositionChanged.connect(self.cursorchanged)

		self.splitter1 = QSplitter(Qt.Orientation.Horizontal)
		self.splitter1.addWidget(self.topleft_frame)
		self.splitter1.addWidget(self.topright)
		self.splitter1.setSizes([600, 600])  # 1:1 比例
		self.splitter1.splitterMoved.connect(self.splitter1_move)

		self.splitter2 = QSplitter(Qt.Orientation.Vertical)
		self.splitter2.addWidget(self.splitter1)
		self.splitter2.addWidget(self.bottom)
		self.splitter2.setSizes([SCREEN_HEIGHT - 200, 100])
		self._splitter2_ratio = self._default_splitter2_ratio(SCREEN_HEIGHT)
		self.splitter2.splitterMoved.connect(self.splitter2_move)
		self.splitter2.setStyleSheet('''
					QSplitter::handle{
					border: transparent;
					background-color: transparent;
					border-image: url("''' + BasePath + '''middle6.png");
					height: 20px;
					border-radius: 4px;
					}
					''')
		self.splitter1.setStyleSheet('''
					QSplitter::handle{
					border: transparent;
					background-color: transparent;
					border-image: url("''' + BasePath + '''middle2.png");
					border-radius: 4px;
					}
					''')

		self.qw0 = QWidget()
		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addStretch()
		hbox.addWidget(self.splitter2)
		hbox.addStretch()
		self.qw0.setLayout(hbox)
		self.qw0.setFixedHeight(SCREEN_HEIGHT - 118)

		self.l1 = QLabel(self)

		img = Image.open(BasePath + 'bottom7.png')
		img_smooth_scaled0 = img.resize((1478, 215), Image.LANCZOS)
		qpixmap0 = QPixmap.fromImage(ImageQt.ImageQt(img_smooth_scaled0))
		self.l1.setPixmap(qpixmap0)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		self.l1.setFixedSize(1478, 215)
		self.l1.move(0, SCREEN_HEIGHT - 215)

		self.btn_sub1 = MacNormalButton(_tr('Open'), self, always_dark=True)
		self.btn_sub1.clicked.connect(self.open_file)
		self.btn_sub1.setFixedSize(210, 22)
		self.btn_sub2 = MacNormalButton(_tr('New'), self, always_dark=True)
		self.btn_sub2.clicked.connect(self.new_file)
		self.btn_sub2.setFixedSize(210, 22)

		self.widget0 = DropdownButton(self, always_dark=True, compact_light=True)   # 紧凑灰色下拉（圆角 6），打字机上一直深色
		self.widget0.setCurrentIndex(0)
		self.widget0.setFixedSize(210, 22)
		self.widget0.setFixedWidth(210)
		tarname3 = "Note 001.md"
		fulldir3 = os.path.join(fulldir1, tarname3)
		if not os.path.exists(fulldir3):
			with open(fulldir3, 'a', encoding='utf-8') as f0:
				f0.write('''This is your very first note stored in [Home]/Library/Application Support/com.ryanthehito.watermelon/WatermelonAppPath/Note 001.md. 

**Just write what you want and start enjoying typing!**

The top-left panel is the realtime Markdown, and the top-right one is the bionic Markdown. You can change the size of each panel.
			
The window will float at top all the time as you focus on typing. If you want to minimize if, press the BLUE BAR.''')
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		if not os.path.exists(fulldir2):
			with open(fulldir2, 'a', encoding='utf-8') as f0:
				f0.write('Note 001||' + fulldir3 + '\n')
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)
		if not os.path.exists(fulldir4):
			with open(fulldir4, 'a', encoding='utf-8') as f0:
				f0.write('0')
		paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = paths.split('\n')
		while '' in pathslist:
			pathslist.remove('')
		namelist = []
		for i in range(len(pathslist)):
			namelist.append(pathslist[i].split('||')[0])
		self.widget0.addItems(namelist)

		# self.btn_mode = QPushButton('Mode: Local', self)
		# self.btn_mode.clicked.connect(self.toggle_notes_mode)
		# self.btn_mode.setFixedSize(120, 20)

		self.btn_notes_folder = MacNormalButton(_tr('Notes Folder'), self, always_dark=True)
		self.btn_notes_folder.clicked.connect(self.open_notes_folder_dialog)
		self.btn_notes_folder.setFixedSize(210, 22)

		self.widget_notes = DropdownButton(self, always_dark=True, compact_light=True)
		self.widget_notes.setFixedSize(210, 22)
		self.widget_notes.setFixedWidth(210)
		self.widget_notes.setEnabled(False)
		self.widget_notes.currentIndexChanged.connect(self.notes_index_change)

		# 以前这里是 Save。保存现在是自动的，这个位置换成“在备忘录里打开这张笔记”（画图、高亮、原生引用这些
		# 只有备忘录自己做得出来，经常要跳过去）。2026-11-21 Ryan：“这个按钮可以改成别的吗”“就按你推荐”。
		self.btn_notes_open = MacNormalButton(_tr('Open in Notes'), self, always_dark=True)
		self.btn_notes_open.clicked.connect(self.open_current_note_in_notes)
		self.btn_notes_open.setFixedSize(210, 22)
		self.btn_notes_open.setEnabled(False)

		self.btn_notes_new = MacNormalButton(_tr('New'), self, always_dark=True)
		self.btn_notes_new.clicked.connect(self.new_notes_note)
		self.btn_notes_new.setFixedSize(210, 22)
		self.btn_notes_new.setEnabled(False)

		self.btn_notes_export = MacNormalButton(_tr('Export'), self, always_dark=True)
		self.btn_notes_export.clicked.connect(self.export_notes_file)
		self.btn_notes_export.setFixedSize(210, 22)
		self.btn_notes_export.setEnabled(False)

		self.btn_sub3 = MacNormalButton(_tr('Export'), self, always_dark=True)
		self.btn_sub3.clicked.connect(self.export_file)
		self.btn_sub3.setFixedSize(210, 22)

		self.btn_sub4 = MacNormalButton(_tr('Clear'), self, always_dark=True)
		self.btn_sub4.clicked.connect(self.clear_all)
		self.btn_sub4.setFixedSize(210, 22)

		# 网页模式的底部按钮行（只在网页模式显示，替换本地/Notes 那一行）
		self.btn_web_back = MacNormalButton('‹', self, always_dark=True)
		self.btn_web_back.setFixedSize(34, 22)
		self.btn_web_back.clicked.connect(self.web_go_back)
		self.btn_web_forward = MacNormalButton('›', self, always_dark=True)
		self.btn_web_forward.setFixedSize(34, 22)
		self.btn_web_forward.clicked.connect(self.web_go_forward)
		self.btn_web_reload = MacNormalButton('↻', self, always_dark=True)
		self.btn_web_reload.setFixedSize(34, 22)
		self.btn_web_reload.clicked.connect(self.web_reload)
		self.web_address = QLineEdit(self)
		self.web_address.setFixedSize(600, 22)
		self.web_address.setPlaceholderText(_tr('Search Google or enter an address'))
		self.web_address.setStyleSheet('''
			QLineEdit {
				border: 1px solid transparent;
				background-color: #404145;
				border-radius: 6px;
				padding: 1px 8px;
				color: #FFFFFF;
				selection-background-color: #0A84FF;
			}
			QLineEdit:focus { border: 1px solid #0A84FF; }
		''')
		self.web_address.returnPressed.connect(self._web_address_submitted)
		self.btn_web_save_local = MacNormalButton(_tr('Save to Local'), self, always_dark=True)
		self.btn_web_save_local.setFixedSize(160, 22)
		self.btn_web_save_local.clicked.connect(self.web_save_to_local)
		self.btn_web_save_notes = MacNormalButton(_tr('Save to Notes'), self, always_dark=True)
		self.btn_web_save_notes.setFixedSize(160, 22)
		self.btn_web_save_notes.clicked.connect(self.web_save_to_notes)
		self._web_row_widgets = (
			self.btn_web_back, self.btn_web_forward, self.btn_web_reload,
			self.web_address, self.btn_web_save_local, self.btn_web_save_notes,
		)

		self.qw1 = QWidget()
		hbox1 = QHBoxLayout(self)
		hbox1.setContentsMargins(0, 0, 0, 10)
		hbox1.addStretch()
		hbox1.addWidget(self.btn_sub1)
		hbox1.addWidget(self.btn_sub2)
		hbox1.addWidget(self.widget0)
		# hbox1.addWidget(self.btn_mode)
		hbox1.addWidget(self.btn_notes_folder)
		hbox1.addWidget(self.btn_notes_new)
		hbox1.addWidget(self.widget_notes)
		hbox1.addWidget(self.btn_notes_export)
		hbox1.addWidget(self.btn_notes_open)
		hbox1.addWidget(self.btn_sub3)
		hbox1.addWidget(self.btn_sub4)
		for widget in self._web_row_widgets:
			hbox1.addWidget(widget)
		hbox1.addStretch()
		self.qw1.setLayout(hbox1)

		vbox3 = QVBoxLayout()
		vbox3.setContentsMargins(0, 0, 0, 0)
		vbox3.addWidget(self.qw0)
		vbox3.addStretch()
		vbox3.addWidget(self.qw1)
		vbox3.addStretch()
		self.setLayout(vbox3)

		self.btn_00 = QPushButton('', self)   # 蓝条：不是玻璃（样式书 5.10），所以不用白色胶囊那个类
		self.btn_00.setAutoDefault(False)
		self.btn_00.clicked.connect(self.pin_a_tab)
		self.btn_00.setFixedHeight(10)
		self.btn_00.setFixedWidth(1200-74-24)
		self.btn_00.setStyleSheet(f'''
				border: 1px outset grey;
				background-color: {get_accent_color_hex()};
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF''')
		self.btn_00.move(160+37+12, SCREEN_HEIGHT - 35)

		self.btn0_1 = GlassButton(
			'', radius=19,
			icon_path=BasePath + 'set2.png',
			momentary=True,
			parent=self
		)
		self.btn0_1.setFixedSize(38, 38)
		self.btn0_1.move(158, SCREEN_HEIGHT - 70)

		self.word_count_label = QLabel('', self)
		self.word_count_label.setStyleSheet('''
			QLabel {
				color: #FFFFFF;
				background-color: transparent;
				font-size: 12px;
				font-weight: 500;
			}
		''')
		self.word_count_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
		self.word_count_label.hide()
		self._position_word_count_label()

		self.btn0_2 = GlassButton(
			'', radius=19,
			icon_path=BasePath + 'repeat.png',
			momentary=True,
			parent=self
		)
		self.btn0_2.setFixedSize(38, 38)
		self.btn0_2.move(1324, SCREEN_HEIGHT - 70)

		self.btn0_sound = GlassButton(
			'', radius=19,
			icon_path=BasePath + 'speaker.png',
			momentary=True,
			parent=self
		)
		self.btn0_sound.setFixedSize(38, 38)
		self.btn0_sound.move(1383, SCREEN_HEIGHT - 200)
		self.btn0_sound.clicked.connect(self.toggle_sound_mode)
		self._start_sound_monitor()

		# 提词器开关：放在声音按钮正下方，样式与声音按钮相同（托盘菜单里的同名项继续保留）
		self.btn0_tp = GlassButton('', radius=19, momentary=True, parent=self)
		self.btn0_tp.setIconPixmap(_teleprompter_icon_pixmap())
		self.btn0_tp.setFixedSize(38, 38)
		self.btn0_tp.move(1383, SCREEN_HEIGHT - 150)
		self.btn0_tp.clicked.connect(self.toggle_teleprompter)

		# 网页模式开关：放在提词器按钮正下方，同样式；网页模式开着时按钮底色加深
		self.btn0_web = GlassButton('', radius=19, momentary=True, parent=self)
		self.btn0_web.setIconPixmap(_web_icon_pixmap())
		self.btn0_web.setFixedSize(38, 38)
		self.btn0_web.move(1383, SCREEN_HEIGHT - 100)
		self.btn0_web.clicked.connect(self.toggle_web_mode)

		# 听课模式没有自己的按钮（Ryan 2026-11-21：“不要你多加一个按钮…好丑”）：编辑区右边缘的把手拉出 / 收回右边的
		# AI 卡片面板，左边缘的把手拉出 / 收回附件列表（鼠标移到边上才出现的圆形把手，同 Strawberry / Tomato）。
		self.lecture_mode_enabled = False
		self.lecture_panel = None
		self.lecture_session = None
		self._lecture_page_source = None
		self.courseware = None
		self._camera_window = None
		self.anki_session = None
		self._anki_dialog = None

		# 左边那一条：这张笔记 / 这个文件里的附件列表（缩略图，按正文里的顺序；点一项在小窗里预览）。
		# 2026-11-21 Ryan：“这个部分是不是可以利用起来，比如变成 notes 中的所有附件的 list”。没有附件时不出现。
		self.attachment_rail = watermelon_attachments.AttachmentRail(self)
		self.attachment_rail.hide()
		self.attachment_rail.opened.connect(self.open_attachment_preview)
		self.attachment_rail.show_in_text.connect(self._show_attachment_in_text)
		self.attachment_rail.files_dropped.connect(self.insert_files_as_attachments)
		self.attachment_rail.remove_requested.connect(self._remove_attachment)
		self.attachment_rail.shots_insert_requested.connect(lambda paths: self._add_courseware_pictures(paths))
		self.attachment_rail.shots_pdf_requested.connect(self._make_courseware_pdf_of)
		self.attachment_rail.shots_delete_requested.connect(lambda paths: [self.courseware.remove(path) for path in paths] if self.courseware is not None else None)
		self.attachment_rail.can_insert = lambda: not self.bottom.isReadOnly() and not self.web_mode_enabled and not self._office_shown()
		self.attachment_rail.note_pdfs = lambda: self._note_pdfs() if watermelon_courseware.pdfkit_available() else []
		self.attachment_rail.can_remove = self._attachment_removable
		self.attachment_rail.shot_requested.connect(lambda: (self._ensure_lecture(), self.courseware.shoot()))
		self.attachment_rail.shot_menu_requested.connect(lambda where: (self._ensure_lecture(), self._show_courseware_menu(where)))
		self._attachment_previews = []
		self._rail_open = _read_switch('attachment_rail.txt', True)
		self._rail_open_empty = False    # 没有附件时被把手拉出来了（只这一次运行）
		self._panel_open = _read_switch('side_panel.txt', False)     # 右边的卡片面板拉出来了没有（和听课模式是两件事）
		# 附件里读者自己标的东西（高亮、批注、便签）：读出来，没显示过的进右边面板，一条只显示一次
		self.mark_watcher = watermelon_marks.MarkWatcher(watermelon_marks.SeenMarks(SettingsPath + 'marks_seen.json'), self)
		self.mark_watcher.new_marks.connect(self._on_new_marks)
		self._place_attachment_rail(SCREEN_HEIGHT)
		# 两个把手：鼠标移到编辑区左 / 右边缘才出现的玻璃圆按钮，点一下拉出 / 收回那一边的面板
		self.side_handles = watermelon_handles.SideHandles(
			self, self._side_column_rect, self._side_panel_rect, self._side_available,
			lambda side: self.attachment_rail.isVisible() if side == 'left' else self._panel_open, self._side_tip)
		self.side_handles.clicked.connect(self._on_side_handle)
		self.side_handles.changed.connect(lambda: self._update_hit_mask() if self._hit_mask_ready else None)
		# 大纲：渲染后的页面右侧的一列刻度（同 Broccoli 的导航条），鼠标停上去向左展开成标题列表，点一项跳过去
		self.outline_rail = watermelon_outline.OutlineRail(self.topleft_frame)
		self.outline_rail.jump_requested.connect(self._jump_to_outline_line)
		self.topleft_frame.installEventFilter(self)
		self.bottom.cursorPositionChanged.connect(self._sync_outline_current)
		self.bottom.viewport().installEventFilter(self)   # 把文件拖进编辑框 = 在那里加一个附件
		self._page_drop_target = None
		self.topleft.installEventFilter(self)              # 拖到排好版的页面上也算（它真正接拖放的是后加的子部件）
		QTimer.singleShot(0, self._watch_page_drops)
		# 编辑区右键多一项「Send to Broccoli」（2026-11-21 Ryan：“就像 tomato 一样用那个公开的接口”）
		self.bottom.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.bottom.customContextMenuRequested.connect(self._show_editor_context_menu)
		self.broccoli_send_done.connect(self._on_broccoli_send_done)
		self.broccoli_write_done.connect(self._on_broccoli_write_done)
		self.write_back = None              # 「在此处续写」等 Broccoli 写完的那些（第一次用时才建）

		self._apply_mode_visibility()

		currentfile = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
		try:
			targetpath = pathslist[currentfile].split('||')[1]
			previewtext = _read_local_text(targetpath)
			self.widget0.setCurrentIndex(currentfile)
		except Exception as e:
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			currentindex = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
			self.widget0.setCurrentIndex(currentindex)
		self.bottom.setText(previewtext)
		self._request_async_preview_render(previewtext, debounce_ms=0)
		self.widget0.currentIndexChanged.connect(self.index_change)
		QTimer.singleShot(0, self._sync_office_view)   # 上次停在 Office 文件 → 启动后直接是 Office 的样子

		w2.setStyleSheet(style_sheet_dark if is_dark_theme(app) else style_sheet_ori)

		self.show()
		self.setFocus()
		self.raise_()
		self.activateWindow()
		self.move(int(SCREEN_WEIGHT / 2) - 760, 0 - SCREEN_HEIGHT)
		self.move_window2(int(SCREEN_WEIGHT / 2) - 760, 0)

		self.l1.raise_()
		self.qw0.raise_()
		self.qw1.raise_()
		self.btn_00.raise_()
		self.btn0_1.raise_()
		self.word_count_label.raise_()
		self.btn0_2.raise_()
		self.btn0_sound.raise_()
		self.btn0_tp.raise_()
		self.btn0_web.raise_()

		self._init_hit_mask()

		# 启动内部组件动画（延迟一小段时间让窗口先开始滑入）
		QTimer.singleShot(200, self._start_intro_animation)


		# w2.checkupdate()
		# if w2.lbl2.text() != 'No Intrenet' and 'ready' in w2.lbl2.text():
		# 	w2.show()

		self._start_mode_autobackup()

	def showEvent(self, event):
		super().showEvent(event)
		keep_out_of_stage_manager(self)
		self._connect_screen_signals()
		self._update_hit_mask(force=True)

	def changeEvent(self, event):
		super().changeEvent(event)
		# 当窗口被激活时（用户从其他应用切换回来），检查 Notes 路径是否有效
		if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
			if self.notes_mode_enabled:
				self._request_notes_cache_refresh()
			self._check_notes_path_on_focus()

	def _check_notes_path_on_focus(self):
		"""当窗口获得焦点时，在后台检查当前 Notes 路径是否仍然有效。
		以前在这里同步跑 osascript，每次切回窗口都会卡住界面（包括这一下点击本身）。"""
		if self.web_mode_enabled:
			return
		if not self.notes_mode_enabled or not self.notes_active:
			return
		if self.notes_awaiting_reselect:
			return  # 已经在等待用户重新选择，不重复检查
		if not self.notes_current_folder or not self.notes_current_title:
			return
		worker = self._notes_focus_check_worker
		if worker is not None and worker.isRunning():
			return
		worker = NoteHtmlReadWorker(self.notes_current_folder, self.notes_current_title, self)
		worker.result.connect(self._on_notes_focus_check_result)
		worker.finished.connect(self._on_notes_focus_check_finished)
		self._notes_focus_check_worker = worker
		worker.start()

	def _on_notes_focus_check_result(self, folder, title, check_html):
		# 结果回来时用户可能已经换了笔记或模式，那就作废
		if not self.notes_mode_enabled or not self.notes_active or self.notes_awaiting_reselect:
			return
		if folder != self.notes_current_folder or title != self.notes_current_title:
			return
		if check_html.strip():
			return
		# 路径无效，锁定编辑器并提示用户
		self._set_notes_active(False)
		self._prompt_notes_reselect(folder, title)

	def _on_notes_focus_check_finished(self):
		worker = self.sender()
		if worker is self._notes_focus_check_worker:
			self._notes_focus_check_worker = None
		if worker is not None:
			worker.deleteLater()

	def _request_notes_cache_refresh(self):
		if self.notes_cache_worker:
			self.notes_cache_worker.request_refresh()

	# ---------- 透明区域点击穿透（与 Broccoli 相同的做法：setMask） ----------
	# 主窗口 1520 宽、与屏幕等高，背景透明。macOS 并不会因为像素透明就把点击交给下面的窗口
	# （实测：不加 mask 时透明处被本窗口接住，加 mask 后才穿透），所以编辑器两侧、打字机底图之外
	# 这些看不见的区域会挡住下面的东西。用 setMask 把窗口形状限制在真正画出来的控件上，
	# 形状以外的点击由系统直接交给下面的窗口。控件移动/缩放/显示/隐藏时（包括各段动画的每一帧）
	# 立即重算，保证动画中的控件不会被裁掉。
	_HIT_MASK_EVENTS = (QEvent.Type.Move, QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Hide)
	HIT_MASK_GLASS_MARGIN = 16  # 圆形玻璃按钮在旧系统上带投影，多留一圈

	def _init_hit_mask(self):
		pixmap = self.l1.pixmap()
		bitmap = pixmap.mask() if pixmap is not None and not pixmap.isNull() else None
		if bitmap is not None and not bitmap.isNull():
			# 打字机底图按实际轮廓（alpha > 0 的像素）算，而不是整个矩形
			self._l1_hit_region = QRegion(bitmap)
		else:
			self._l1_hit_region = QRegion(self.l1.rect())
		self._hit_mask_row_widgets = (
			self.btn_sub1, self.btn_sub2, self.widget0,
			self.btn_notes_folder, self.btn_notes_new, self.widget_notes,
			self.btn_notes_export, self.btn_notes_open,
			self.btn_sub3, self.btn_sub4,
		) + self._web_row_widgets
		tracked = (
			self.qw0, self.splitter2, self.l1, self.qw1,
			self.btn_00, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web, self.word_count_label,
		) + self._hit_mask_row_widgets
		for widget in tracked:
			widget.installEventFilter(self)
		self._hit_mask_ready = True
		self._update_hit_mask()

	def _hit_mask_rect(self, widget, margin=0):
		rect = QRect(widget.mapTo(self, QPoint(0, 0)), widget.size())
		return QRegion(rect.adjusted(-margin, -margin, margin, margin))

	CONTENT_BLOCK_RADIUS = 4   # 文字框、预览框的圆角；网页区、Office 区和它们一样

	def _hit_mask_rounded(self, widget):
		"""网页区 / Office 区是网页内容，自己画不出圆角（四个直角会盖住边框的圆角）。把窗口形状在这一块的四个角
		切成和文字框一样的圆角：内容被“包”在圆角框里，不露直角（2026-11-20 Ryan：“把窗口包起来”“这个直角的
		边角非常糟糕，和其他的大小不一样”）。"""
		rect = QRectF(QRect(widget.mapTo(self, QPoint(0, 0)), widget.size()))
		path = QPainterPath()
		path.addRoundedRect(rect, self.CONTENT_BLOCK_RADIUS, self.CONTENT_BLOCK_RADIUS)
		return QRegion(path.toFillPolygon().toPolygon())

	def _update_hit_mask(self, force=False):
		if not self._hit_mask_ready:
			return
		region = QRegion()
		if self.qw0.isVisible():
			if self.splitter2.isVisible():
				region = region.united(self._hit_mask_rect(self.splitter2))
			if self.web_panel is not None and self.web_panel.isVisible():
				region = region.united(self._hit_mask_rounded(self.web_panel))
			if self.office_panel is not None and self.office_panel.isVisible():
				region = region.united(self._hit_mask_rounded(self.office_panel))
		# 两边的玻璃面板和把手：点击形状用整块矩形，不切圆角。窗口的点击形状只能由整点的小方块拼成，切圆角会把
		# 系统玻璃自己画的平滑圆角切成一级一级的台阶（2026-11-21 Ryan：“两个液态玻璃的 panel 会有锯齿状的边缘”）。
		# 圆角外侧那几个透明的小角因此点不穿，几乎碰不到。
		rail = getattr(self, 'attachment_rail', None)
		if rail is not None and rail.isVisible():
			region = region.united(QRegion(rail.geometry()))
		handles = getattr(self, 'side_handles', None)
		if handles is not None:
			for handle_rect in handles.visible_rects():
				region = region.united(QRegion(handle_rect.adjusted(-2, -2, 2, 2)))
		lecture = getattr(self, 'lecture_panel', None)
		if lecture is not None and lecture.isVisible():
			region = region.united(QRegion(lecture.geometry()))
		if self.l1.isVisible():
			region = region.united(self._l1_hit_region.translated(self.l1.pos()))
		for widget in self._hit_mask_row_widgets:
			if widget.isVisible():
				region = region.united(self._hit_mask_rect(widget))
		if self.btn_00.isVisible():
			region = region.united(self._hit_mask_rect(self.btn_00, 4))
		for widget in (self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web):
			if widget.isVisible():
				region = region.united(self._hit_mask_rect(widget, self.HIT_MASK_GLASS_MARGIN))
		if self.word_count_label.isVisible():
			region = region.united(self._hit_mask_rect(self.word_count_label))
		region = region.intersected(QRegion(self.rect()))
		if region.isEmpty():
			# 不能 clearMask：那样整个透明窗口又会重新挡住点击。留 1 个像素即可。
			region = QRegion(0, 0, 1, 1)
		if force:
			self.clearMask()
		self.setMask(region)

	def eventFilter(self, obj, event):
		on_editor = hasattr(self, 'bottom') and obj is self.bottom.viewport()
		on_page = obj is getattr(self, '_page_drop_target', None) and obj is not None
		if (on_editor or on_page) and event.type() in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
			# 拖进编辑框的文件 = 在放下的位置加一个附件（图片、PDF、视频、Word……）；左边列表里拖来的截图 = 在那里
			# 作为图片插进去（Ryan 2026-11-24：“拖动也能插入”）。拖到上面排好版的页面上 = 放在笔记最后（页面上的位置
			# 对不回正文）。别的拖放照旧
			data = event.mimeData()
			shots = [p for p in bytes(data.data(watermelon_attachments.SHOTS_MIME)).decode('utf-8', 'replace').split('\n') if p] if data.hasFormat(watermelon_attachments.SHOTS_MIME) else []
			paths = [] if shots else ([url.toLocalFile() for url in data.urls() if url.isLocalFile() and os.path.isfile(url.toLocalFile())] if data.hasUrls() else [])
			if (paths or shots) and not self.bottom.isReadOnly() and not self.web_mode_enabled and not self._office_shown():
				event.setDropAction(Qt.DropAction.CopyAction)
				event.accept()
				if event.type() == QEvent.Type.Drop:
					if on_editor:
						cursor = self.bottom.cursorForPosition(event.position().toPoint())
					else:
						cursor = self.bottom.textCursor()
						cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.End)
					if shots:
						cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.EndOfBlock)
						self._add_courseware_pictures(shots, at=cursor.position())
					else:
						self.bottom.setTextCursor(cursor)
						self.insert_files_as_attachments(paths)
				return True
		if hasattr(self, 'topleft') and obj is self.topleft and event.type() == QEvent.Type.ChildAdded:
			QTimer.singleShot(0, self._watch_page_drops)      # 网页视图的内容是它后来加进来的子部件
		if hasattr(self, 'outline_rail') and obj is self.topleft_frame and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
			self._place_outline_rail()
		if self._hit_mask_ready and event.type() in self._HIT_MASK_EVENTS:
			self._sync_attachment_rail()
			self._update_hit_mask()
		return super().eventFilter(obj, event)

	# ---------- 右键：发给 Broccoli ----------
	def _show_editor_context_menu(self, point):
		"""编辑框的右键菜单 = 系统原来那几项（剪切 / 拷贝 / 粘贴……）+ 一条分隔线 + Send to Broccoli。"""
		menu = style_watermelon_context_menu(self.bottom.createStandardContextMenu())
		menu.addSeparator()
		send = menu.addAction(_tr('Send to Broccoli'))
		send.setEnabled(bool(self.bottom.toPlainText().strip()))
		ask = menu.addAction(_tr('Ask Broccoli…'))
		write = menu.addAction(_tr('Write Here with Broccoli…'))
		write.setEnabled(not self.bottom.isReadOnly())
		anki = menu.addAction(_tr('Make Anki Cards…'))
		chosen = menu.exec(self.bottom.mapToGlobal(point))
		if chosen is ask:
			self.ask_broccoli()
		elif chosen is write:
			self.write_here_with_broccoli(point)
		elif chosen is send:
			self.send_to_broccoli()
		elif chosen is anki:
			self.make_anki_cards()

	BROCCOLI_STAGE_MAX_FILES = 20      # Broccoli 的公开接口一次最多收 20 个附件

	def send_to_broccoli(self):
		"""选中的文字（没选就是整篇）当成背景资料交给 Broccoli，不是问题（Ryan 2026-11-24：“不是要你当成问题直接发送，
		而是让你把选中的文字，如果没有选中的那就是全部的文字，当成背景语境，然后用户再去 broccoli 里问问题”）：
		存成一个 .md 文件（名字 = 笔记名），Broccoli 出来、开一个空白新对话（发出去时进 “Watermelon” 分组），文件在
		它的附件托盘里，光标在输入框里，什么都不跑，等用户自己问。Broccoli 没开就打开再交。在后台线程里做。"""
		selected = self.bottom.textCursor().selectedText().replace('\u2029', '\n').strip()
		text = selected or self.bottom.toPlainText().strip()
		if not text or not self._broccoli_ready(_tr('Sending to Broccoli')):
			return
		if self.notes_mode_enabled:
			name = self.notes_current_title or ''
		else:
			name = self.widget0.currentText()
		safe = re.sub(r'[\\/:*?"<>|\n]+', ' ', name or 'Watermelon').strip()[:60] or 'Watermelon'
		file_name = (_tr('%s (selection)') % safe if selected else safe) + '.md'
		folder = os.path.join(WATERMELON_CACHE_ROOT, 'Broccoli', 'Context', datetime.now().strftime('%Y%m%d-%H%M%S'))
		metadata = {'watermelon_document': name, 'watermelon_selection': bool(selected)}
		# 这段文字里引用的本地文件（图片、PDF、Word……）本身也交过去，当附件，不只是一行路径文字
		# （Ryan 2026-11-24：“如果 notes 里有其他图片啊附件的路径，broccoli 得能够把这些路径的文件当成附件，而不是纯文本”）
		files = list(dict.fromkeys(item['path'] for item in watermelon_attachments.attachments_in(text, self._attachment_base_dir())))
		files = [path for path in files if os.path.isfile(path)][:self.BROCCOLI_STAGE_MAX_FILES - 1]
		self._show_mode_toast(_tr('Sending to Broccoli…'))

		def work():
			try:
				os.makedirs(folder, exist_ok=True)
				path = os.path.join(folder, file_name)
				with open(path, 'w', encoding='utf-8') as handle:
					handle.write(text + '\n')
				ok, detail = watermelon_broccoli.stage([path] + files, title=name, metadata=metadata)
			except Exception as exc:
				ok, detail = False, str(exc)
			self.broccoli_send_done.emit(bool(ok), str(detail))

		threading.Thread(target=work, daemon=True, name='watermelon-send-broccoli').start()

	# ---------- 右键：让 Broccoli 在此处续写 ----------
	def _ensure_write_back(self):
		if self.write_back is None:
			folder = os.path.join(WATERMELON_CACHE_ROOT, 'Broccoli', 'WriteBack')
			os.makedirs(folder, exist_ok=True)
			self.write_back = broccoli_write_back.WriteBack(
				folder, self._courseware_note_key,
				lambda key: self.bottom if key and key == self._courseware_note_key() and not self.bottom.isReadOnly() else None,
				parent=self)
			self.write_back.typed.connect(lambda _key, count: self._show_mode_toast(_tr('Broccoli wrote %d characters here') % count))
			self.write_back.waiting.connect(lambda _key: self._show_mode_toast(_tr("Broccoli's text is ready: it goes in when that note is open again")))
			self.write_back.dropped.connect(self._on_write_back_dropped)
		return self.write_back

	def write_here_with_broccoli(self, point=None):
		"""编辑框右键「Write Here with Broccoli…」（Ryan 2026-11-25：“让 broccoli 在此处续写，然后和 ask 差不多，也是把内容加为
		背景，然后弹出 broccoli 窗口，用户输入写作需求，然后完成之后 broccoli 内有记录，而且还自动把输出的内容 type 到对应的
		watermelon 的位置”）。整篇（在右键的位置放一个记号）当背景资料交给 Broccoli，同 Send to Broccoli；在 Broccoli 里说要写
		什么，那个对话照常留在 Broccoli 里；写完的字由 broccoli_write_back 一段段打进这里记住的位置。位置 = 右键点的地方
		（点在选中的字上 = 选中的字后面）。"""
		if self.bottom.isReadOnly() or not self._broccoli_ready(_tr('Writing with Broccoli')):
			return
		cursor = self.bottom.textCursor()
		if point is not None:
			clicked = self.bottom.cursorForPosition(point).position()
			if cursor.hasSelection() and cursor.selectionStart() <= clicked <= cursor.selectionEnd():
				position = cursor.selectionEnd()
			else:
				position = clicked
				cursor.setPosition(position)
				self.bottom.setTextCursor(cursor)       # 光标放到要写的地方，看得到
		else:
			position = cursor.selectionEnd()
		text = self.bottom.toPlainText()
		index = broccoli_write_back.to_py(text, position)
		if self.notes_mode_enabled:
			name = self.notes_current_title or ''
		else:
			name = self.widget0.currentText()
		safe = re.sub(r'[\\/:*?"<>|\n]+', ' ', name or 'Watermelon').strip()[:60] or 'Watermelon'
		writer = self._ensure_write_back()
		request_id = writer.begin(self.bottom, position, self._courseware_note_key())
		folder = os.path.join(WATERMELON_CACHE_ROOT, 'Broccoli', 'Context', datetime.now().strftime('%Y%m%d-%H%M%S'))
		files = list(dict.fromkeys(item['path'] for item in watermelon_attachments.attachments_in(text, self._attachment_base_dir())))
		files = [path for path in files if os.path.isfile(path)][:self.BROCCOLI_STAGE_MAX_FILES - 1]
		body = broccoli_write_back.material(text, index)
		metadata = {'watermelon_document': name, 'watermelon_write_here': True}
		self._show_mode_toast(_tr('Sending to Broccoli…'))

		def work():
			try:
				os.makedirs(folder, exist_ok=True)
				path = os.path.join(folder, safe + '.md')
				with open(path, 'w', encoding='utf-8') as handle:
					handle.write(body + '\n')
				ok, detail = watermelon_broccoli.stage(
					[path] + files, title=name, metadata=metadata,
					extra_fields={'write_back': {'marker': broccoli_write_back.MARKER}, 'reply_to': writer.reply_dir, 'id': request_id})
			except Exception as exc:
				ok, detail = False, str(exc)
			self.broccoli_write_done.emit(bool(ok), str(detail), request_id)

		threading.Thread(target=work, daemon=True, name='watermelon-write-here').start()
		return request_id

	def _on_broccoli_write_done(self, ok, detail, request_id):
		if ok:
			self._show_mode_toast(_tr('In Broccoli now: say what to write, it is typed in here when done'))
			return
		if self.write_back is not None:
			self.write_back.forget(request_id)
		self._on_broccoli_send_done(ok, detail)

	def _on_write_back_dropped(self, status):
		if status in ('cancelled', 'stopped'):
			self._show_mode_toast(_tr('Writing with Broccoli was cancelled'))
		else:
			self._show_mode_toast(_tr("Broccoli didn't write anything"))

	def _on_broccoli_send_done(self, ok, detail):
		if ok:
			self._show_mode_toast(_tr('In Broccoli now: ask your question there'))
		elif detail == 'not_installed':
			self._show_mode_toast(_tr('Broccoli is not on this Mac'))
		else:
			logging.warning('Sending to Broccoli failed: %s', detail)
			self._show_mode_toast(_tr("Couldn't reach Broccoli"))

	# ---------- Anki 卡片 ----------
	def _ensure_anki(self):
		if self.anki_session is None:
			cache = os.path.join(WATERMELON_CACHE_ROOT, 'Anki')
			store = watermelon_anki.AnkiStore(os.path.join(WATERMELON_DATA_DIR, 'Anki'))
			self.anki_session = watermelon_anki.AnkiSession(store, os.path.join(cache, 'Replies'), os.path.join(cache, 'Pages'), parent=self)
			self.anki_session.done.connect(self._on_anki_done)
			self.anki_session.failed.connect(self._on_anki_failed)

	def make_anki_cards(self):
		"""从选中的文字（没选 = 整篇；网页模式 = 网页里选中的；Office 文件 = 文件里选中的）加上可选的附件页，
		让 Broccoli 做 Anki 卡片，存进一个牌组文件夹。先出一个小窗选牌组、卡片种类、带哪些附件。"""
		if not self._broccoli_ready(_tr('Making Anki cards')):
			return
		self._ensure_anki()
		if self._anki_dialog is not None:
			self._anki_dialog.raise_()
			self._anki_dialog.activateWindow()
			return
		if self.web_mode_enabled:
			text = self._web_selected_text.replace('\u2029', '\n').strip()
			if not text:
				self._show_mode_toast(_tr('Select text on the page first'))
				return
			self._open_anki_dialog(text, _tr('From the text selected on the web page (%d characters)') % len(text), [], '')
			return
		if self._office_shown():
			view = getattr(self.office_panel, '_view', None)
			name = os.path.splitext(os.path.basename(self._current_local_file_path() or ''))[0]

			def got(selection):
				text = str((selection or {}).get('text', '') or '').strip()
				if not text:
					self._show_mode_toast(_tr('Select text in the document first'))
					return
				self._open_anki_dialog(text, _tr('From the text selected in the document (%d characters)') % len(text), [], name)

			if view is None:
				got({})
			else:
				view.fetch_selection(got)
			return
		selected = self.bottom.textCursor().selectedText().replace('\u2029', '\n').strip()
		whole = self.bottom.toPlainText()
		text = selected or whole.strip()
		label = (_tr('From the selected text (%d characters)') if selected else _tr('From the whole note (%d characters)')) % len(text)
		self._open_anki_dialog(text, label, self._anki_attachments(whole), self._lecture_document_name())

	def _anki_attachments(self, markdown_text):
		"""这张笔记里能发给模型看的附件：PDF（要选页）和图片，加上还没存的课件截图。"""
		from PyQt6.QtPdf import QPdfDocument
		items = [item for item in watermelon_attachments.attachments_in(markdown_text, self._attachment_base_dir())
				 if item['kind'] in ('pdf', 'image')]
		if self.courseware is not None:
			items += self.courseware.items()
		out = []
		for item in items[:8]:
			item = dict(item)
			if item['kind'] == 'pdf':
				document = QPdfDocument(None)
				document.load(item['path'])
				item['pages'] = document.pageCount()
				document.close()
				window = next((w for w in self._attachment_previews if w.path == item['path']), None)
				item['page'] = (window.current_page() + 1) if window is not None else 1
				if not item['pages']:
					continue
			out.append(item)
		return out

	def _open_anki_dialog(self, text, label, attachments, suggested_deck):
		dialog = watermelon_anki.AnkiDialog(self.anki_session.store.decks(), text, label, attachments, suggested_deck)
		dialog.generate.connect(lambda choices, t=text: self._start_anki_request(t, choices))
		dialog.show_folder.connect(self._show_anki_folder)
		dialog.destroyed.connect(lambda *_a: setattr(self, '_anki_dialog', None))
		self._anki_dialog = dialog
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		return dialog

	def _start_anki_request(self, text, choices):
		"""选好的附件页先一页一页画成图（每画一页让界面喘口气），再一起发给 Broccoli。"""
		from PyQt6.QtPdf import QPdfDocument
		session = self.anki_session
		jobs = []
		for item, pages in choices['attachments']:
			if item['kind'] == 'pdf':
				jobs += [(item['path'], page) for page in pages]
			else:
				jobs.append((item['path'], None))
		jobs = jobs[:watermelon_anki.MAX_PAGES]
		pictures = []
		documents = {}
		stamp = datetime.now().strftime('%H%M%S%f')
		language = watermelon_lecture.LectureSettings(SettingsPath + 'lecture.json').get('language')
		self._show_mode_toast(_tr('Asking Broccoli for cards…'))

		def step():
			if not jobs:
				for document in documents.values():
					document.close()
				session.request(choices['deck'], text, choices['kind'], choices['count'], pictures, language, self._lecture_document_name())
				return
			path, page = jobs.pop(0)
			try:
				if page is None:
					pictures.append(path)
				else:
					document = documents.get(path)
					if document is None:
						document = documents[path] = QPdfDocument(self)
						document.load(path)
					size = document.pagePointSize(page)
					scale = 1400.0 / max(1.0, size.width())
					image = document.render(page, QSize(int(size.width() * scale), int(size.height() * scale)))
					white = QImage(image.size(), QImage.Format.Format_RGB32)
					white.fill(QColor('#FFFFFF'))
					painter = QPainter(white)
					painter.drawImage(0, 0, image)
					painter.end()
					os.makedirs(session.pages_dir, exist_ok=True)
					target = os.path.join(session.pages_dir, '%s-%d-p%d.png' % (stamp, len(pictures), page + 1))
					if white.save(target, 'PNG'):
						pictures.append(target)
			except Exception:
				logging.exception('Rendering a page for the Anki request failed.')
			QTimer.singleShot(0, step)

		QTimer.singleShot(0, step)

	def _show_anki_folder(self, deck):
		folder = self.anki_session.store.folder(deck) if deck else self.anki_session.store.root
		os.makedirs(folder, exist_ok=True)
		subprocess.Popen(['/usr/bin/open', folder])

	def _on_anki_done(self, deck, added, total):
		show, ok = _tr('Show in Finder'), _tr('OK')
		if added:
			title = _tr('%d cards added to “%s”') % (added, deck)
		else:
			title = _tr('No new cards for “%s”') % deck
		answer = watermelon_choice(self, title,
								   _tr('The deck has %d cards now. To use them, import the files in its folder into Anki (File › Import).') % total,
								   [ok, show], default=ok, escape=ok)
		if answer == show:
			self._show_anki_folder(deck)

	def _on_anki_failed(self, reason):
		texts = {'not_installed': _tr('Broccoli is not on this Mac'), 'no_answer': _tr("Couldn't reach Broccoli"),
				 'no_cards': _tr("Broccoli's answer had no cards in it. Please try again."),
				 'failed': _tr("Broccoli couldn't answer")}
		watermelon_alert(self, _tr("Couldn't make the Anki cards"), texts.get(reason, texts['failed']))

	# ---------- 两边的把手 ----------
	def _side_column_rect(self):
		"""中间那一列（两栏预览加文字框 / 网页 / Office 文件）在窗口里的位置；主窗口收起时 = 空（那时没有把手）。"""
		if not self.qw0.isVisible():
			return QRect()
		for block in (self.splitter2, self.web_panel, self.office_panel):
			if block is not None and block.isVisible():
				return QRect(block.mapTo(self, QPoint(0, 0)), block.size())
		return QRect()

	def _side_panel_rect(self, side):
		panel = self.attachment_rail if side == 'left' else self.lecture_panel
		return panel.geometry() if panel is not None and panel.isVisible() else None

	def _side_available(self, side):
		# 左边：笔记在显示时（没有附件也可以拉出来用上面的相机）；右边：一直可以
		return self.splitter2.isVisible() if side == 'left' else True

	def _side_tip(self, side):
		if side == 'left':
			return _tr('Hide attachments') if self.attachment_rail.isVisible() else _tr('Show attachments')
		return _tr('Hide cards') if self._panel_open else _tr('Show cards')

	def _on_side_handle(self, side):
		if side == 'left':
			if self.attachment_rail.items():
				self._rail_open = not self.attachment_rail.isVisible()
				_write_switch('attachment_rail.txt', self._rail_open)
			else:
				self._rail_open_empty = not self.attachment_rail.isVisible()
			self._sync_attachment_rail()
		else:
			self._set_panel_open(not self._panel_open)

	# ---------- 附件里读者自己标的东西 → 右边的卡片 ----------
	def _refresh_marks(self, markdown_text=None):
		"""现在该看哪些文件：笔记里的 PDF / Word / Excel / PowerPoint 附件；编辑区开着一份 Office 文件时就是它。"""
		if not hasattr(self, 'mark_watcher'):
			return
		if self._office_shown():
			files = [self._current_local_file_path() or '']
		elif self.web_mode_enabled:
			files = []
		else:
			if markdown_text is None:
				markdown_text = self.bottom.toPlainText()
			files = [item['path'] for item in watermelon_attachments.attachments_in(markdown_text, self._attachment_base_dir())
					 if item['kind'] in ('pdf', 'office')]
		self.mark_watcher.set_files([path for path in files if path])

	def _on_new_marks(self, path, marks):
		"""没显示过的标记：一条一张卡片进右边面板。面板收着就不弹出来，只让右把手带着小圆点留在那里。"""
		self._ensure_lecture()
		store, document, name = self.lecture_session.store, self._lecture_document_name(), os.path.basename(path)
		kinds = {'Highlight': _tr('Highlight'), 'Underline': _tr('Underline'), 'Strikethrough': _tr('Strikethrough'),
				 'Note': _tr('Note'), 'Comment': _tr('Comment'), 'Speaker notes': _tr('Speaker notes')}
		made = ''
		for mark in reversed(marks):                 # 存的时候新的在前：倒着加，面板里就是文件里的顺序
			kind = kinds.get(watermelon_marks.KINDS.get(mark['kind'], mark['kind']), mark['kind'])
			label = '%s · %s' % (('%s %s' % (name, mark['where'])).strip(), kind)
			title = mark['text'] or (mark['note'] if len(mark['note']) <= 60 else '')
			body = mark['note'] if mark['text'] or len(mark['note']) > 60 else ''
			if mark.get('who') and body:
				body = '%s\n— %s' % (body, mark['who'])
			made = store.add(title, body, page=label, source='mark', document=document, file=path, file_page=mark.get('page', -1))['id']
		self.lecture_session.cards_changed.emit(made if len(marks) == 1 else '')
		if not (self.lecture_panel is not None and self.lecture_panel.isVisible()):
			self.side_handles.set_attention('right', True)

	def _show_mark_card(self, card):
		"""卡片 → 那份附件的那一页（在预览小窗里）。"""
		path = card.get('file') or ''
		if not os.path.isfile(path) or watermelon_attachments.kind_of(path) != 'pdf':
			if os.path.isfile(path):
				self.open_attachment_preview({'path': path, 'name': os.path.basename(path), 'kind': watermelon_attachments.kind_of(path), 'offset': -1})
			return
		window = self.open_attachment_preview({'path': path, 'name': os.path.basename(path), 'kind': 'pdf', 'offset': -1})
		if window is not None and int(card.get('file_page', -1)) >= 0:
			QTimer.singleShot(150, lambda: window.go_to_page(int(card.get('file_page', 0))))

	# ---------- 大纲（渲染页面右侧的刻度） ----------
	def _place_outline_rail(self):
		frame = self.topleft_frame
		self.outline_rail.set_anchor(frame.width() - 16, frame.height() // 2, frame.height() - 40)

	def _sync_outline(self, markdown_text=None):
		if not hasattr(self, 'outline_rail'):
			return
		self.outline_rail.set_markdown(self.bottom.toPlainText() if markdown_text is None else markdown_text)
		self._place_outline_rail()
		self._sync_outline_current()

	def _sync_outline_current(self):
		if hasattr(self, 'outline_rail'):
			self.outline_rail.set_current_line(self.bottom.textCursor().blockNumber())

	def _jump_to_outline_line(self, line):
		block = self.bottom.document().findBlockByNumber(int(line))
		if not block.isValid():
			return
		cursor = self.bottom.textCursor()
		cursor.setPosition(block.position())
		self.bottom.setTextCursor(cursor)
		bar = self.bottom.verticalScrollBar()
		bar.setValue(bar.value() + self.bottom.cursorRect().top() - 8)   # 标题那一行到编辑框顶上
		self.bottom.setFocus()

	# ---------- 左边的附件列表和预览小窗 ----------
	def _place_attachment_rail(self, screen_height):
		"""编辑区左边那一条：从编辑区顶上到打字机左边的花纹上方。"""
		if not hasattr(self, 'attachment_rail'):
			return
		self.attachment_rail.move(8, 12)       # 左边空条 0–143：离窗口边 8、离编辑区 8，刚好填满，不压到编辑区
		self.attachment_rail.setFixedHeight(max(160, int(screen_height) - 310))
		self._side_panels_screen_height = int(screen_height)
		self._place_lecture_panel(screen_height)

	def _attachment_base_dir(self):
		if self.notes_mode_enabled:
			return ''
		path = self._current_local_file_path() or ''
		return os.path.dirname(path) if path else ''

	def _refresh_attachment_rail(self, markdown_text=None):
		if not hasattr(self, 'attachment_rail'):
			return
		if markdown_text is None:
			markdown_text = self.bottom.toPlainText()
		items = watermelon_attachments.attachments_in(markdown_text, self._attachment_base_dir())
		self._ensure_courseware()
		self.courseware.set_note(self._courseware_note_key(), self._lecture_document_name())   # 换了笔记 = 那张笔记自己的截图
		items = items + self.courseware.items()          # 还没放进笔记的截图排在后面
		self.attachment_rail.set_items(items)
		self._sync_outline(markdown_text)
		writer = getattr(self, 'write_back', None)
		if writer is not None and writer.pending() and not writer.typing():
			QTimer.singleShot(0, writer.try_waiting)      # 换到了在等 Broccoli 写字的那张笔记
		self._sync_attachment_rail()
		if self.lecture_session is not None:
			self.lecture_session.set_document(self._lecture_document_name())   # 换了笔记 = 另一组卡片、另一条对话
		self._refresh_marks(markdown_text)

	def _sync_attachment_rail(self):
		"""笔记在显示（不是网页模式也不是 Office 文件）时：有附件 = 照把手的开关（默认拉出）；没有附件 = 只有用把手
		拉出来时才出现（上面的相机可以截图 / 拍照加附件）。"""
		rail = getattr(self, 'attachment_rail', None)
		if rail is None:
			return
		opened = self._rail_open if rail.items() else self._rail_open_empty
		wanted = opened and self.qw0.isVisible() and self.splitter2.isVisible() and not self.web_mode_enabled
		if wanted != rail.isVisible():
			rail.setVisible(wanted)
			if wanted:
				rail.raise_()
			if self._hit_mask_ready:
				QTimer.singleShot(0, self._update_hit_mask)
		self._sync_lecture_panel()
		if getattr(self, 'side_handles', None) is not None and self._side_column_rect().isEmpty():
			self.side_handles.hide_now()      # 编辑区不在了（收起、网页模式、Office 文件）：把手也不在

	# ---------- 右边：听课模式的 AI 卡片面板 ----------
	def _lecture_document_name(self):
		return (self.notes_current_title or '') if self.notes_mode_enabled else self.widget0.currentText()

	def _ensure_lecture(self):
		if self.lecture_session is not None:
			return
		cache = os.path.join(WATERMELON_CACHE_ROOT, 'Lecture')
		settings = watermelon_lecture.LectureSettings(SettingsPath + 'lecture.json')
		store = watermelon_lecture.CardStore(SettingsPath + 'lecture_cards.json')
		self.lecture_session = watermelon_lecture.LectureSession(
			store, settings, os.path.join(cache, 'Replies'), os.path.join(cache, 'Pages'), parent=self)
		self.lecture_panel = watermelon_lecture.LecturePanel(self.lecture_session, self)
		self.lecture_panel.hide()
		self.lecture_panel.insert_requested.connect(self._insert_lecture_card)
		self.lecture_panel.show_requested.connect(self._show_mark_card)
		self.lecture_panel.ask_requested.connect(self._open_ask_dialog)
		self.lecture_session.set_document(self._lecture_document_name())
		self.lecture_session.set_sources(self._lecture_note_text, self._lecture_page, self._lecture_focus)
		self.lecture_panel.clear_archive_requested.connect(self._clear_lecture_archive)
		self._place_lecture_panel(self._side_panels_screen_height)   # 和左边的列表同一个高度
		self._ensure_courseware()

	def _ensure_courseware(self):
		"""还没放进笔记的截图 / 照片：按笔记分开存在 Watermelon 自己的资料文件夹里（不放系统缓存），重启后还在，
		只有用户自己插进笔记、合成 PDF 或删掉才离开列表。和听课模式无关，一开始就有。"""
		if self.courseware is not None:
			return
		self.courseware = watermelon_courseware.Courseware(os.path.join(WATERMELON_APPLICATION_SUPPORT_DIR, 'Screenshots'), parent=self)
		self.courseware.changed.connect(self._on_courseware_changed)
		self.courseware.failed.connect(lambda: self._show_mode_toast(_tr("Couldn't take the screenshot")))
		self.courseware.pdf_done.connect(self._on_courseware_pdf)
		self.courseware.pictures_done.connect(self._on_courseware_pictures)

	def _courseware_note_key(self):
		"""截图属于哪张笔记：备忘录 = 那张笔记的编号（没有就用文件夹 + 标题）；本地文件 = 文件路径。"""
		if self.notes_mode_enabled:
			folder, title = self.notes_current_folder or '', self.notes_current_title or ''
			if not title:
				return ''
			current = self.widget_notes.currentData() if hasattr(self, 'widget_notes') else None
			note_id = str(current.get('id') or '') if isinstance(current, dict) and (current.get('title') or '(Untitled)') == title else ''
			note_id = note_id or _note_id_for(folder, title)   # 编号跟着笔记走，改了标题也还是这张
			return ('notes:' + note_id) if note_id else ('notes:%s/%s' % (folder, title))
		path = self._current_local_file_path() or ''
		return ('file:' + os.path.abspath(path)) if path else ''

	# ---------- 截图当课件：同一块地方再截一张；结束时合成 PDF 存进笔记 ----------
	def _on_courseware_changed(self, path):
		self._refresh_attachment_rail()
		if path:
			self._show_mode_toast(_tr('Screenshot %d taken') % len(self.courseware.shots))
			self._lecture_page_source = {'path': path, 'label': self.courseware.label_of(path)}
			if self.lecture_mode_enabled:
				self.lecture_session.page_turned()

	def _note_pdfs(self):
		return [item for item in watermelon_attachments.attachments_in(self.bottom.toPlainText(), self._attachment_base_dir())
				if item['kind'] == 'pdf']

	def _show_courseware_menu(self, where):
		menu = style_watermelon_context_menu(QMenu(self))
		count = len(self.courseware.shots)
		shoot = menu.addAction(_tr('Take Screenshot'))
		area = menu.addAction(_tr('Choose Area Again…'))
		area.setEnabled(self.courseware.region is not None)
		photo = menu.addAction(_tr('Take Photo with Camera…'))
		add = menu.addAction(_tr('Add Pictures…'))
		# 插入 / 合成 PDF / 删除不在相机按钮上：在列表里每张截图上右键（可多选）、拖进笔记
		# （Ryan 2026-11-24：“不要在按钮上右键，你肯定是每一个图片上右键选择插入，拖动也能插入，然后多选右键可以生成 pdf，单图也能删除”）
		chosen = menu.exec(where)
		if chosen is shoot:
			self.courseware.shoot()
		elif chosen is area:
			self.courseware.pick_region()
		elif chosen is photo:
			self.open_camera_window()
		elif chosen is add:
			paths, _filter = QFileDialog.getOpenFileNames(self, _tr('Add Pictures…'), str(Path.home()),
														  'Images (*.png *.jpg *.jpeg *.heic *.tiff *.gif *.bmp)')
			self.courseware.add_pictures(paths)

	def open_camera_window(self):
		"""用这台 Mac 的摄像头（自带的、拍桌面的、iPhone 接力相机）拍纸：每拍一张，自动找到纸、拉正、变清晰，
		作为课件的一页排进左边的列表。窗口留着可以接着拍下一张。"""
		self._ensure_lecture()
		if self._camera_window is not None:
			self._camera_window.show()
			self._camera_window.raise_()
			self._camera_window.activateWindow()
			return self._camera_window
		settings = self.lecture_session.settings
		window = watermelon_scan.CameraWindow(remembered=settings.get('camera'))
		window.photo_taken.connect(self.courseware.add_photo)
		window.camera_chosen.connect(lambda name: settings.set('camera', name))
		window.closed.connect(lambda: setattr(self, '_camera_window', None))
		start = self.mapToGlobal(QPoint(420, 120))
		window.move(start)
		self._camera_window = window
		window.show()
		window.raise_()
		window.activateWindow()
		return window

	def _courseware_note_folder(self):
		"""截图变成笔记附件时放哪儿：备忘录 = 缓存里（存进备忘录时它自己拷一份）；本地文件 = 笔记旁边。"""
		if self.notes_mode_enabled:
			return os.path.join(WATERMELON_CACHE_ROOT, 'Lecture', 'Courseware', 'pdf')
		return self._attachment_base_dir() or WATERMELON_DATA_DIR

	def _add_courseware_pictures(self, paths=None, at=None):
		"""截图不合成 PDF，按截的顺序一张一行图片放进笔记（paths = 只这几张）：at = 正文里的位置（拖进来放下的地方，
		放在那一段后面），没有 = 笔记最后。"""
		if self.courseware is None or not self.courseware.shots or self.bottom.isReadOnly() or self.web_mode_enabled or self._office_shown():
			return
		name = re.sub(r'[\\/:*?"<>|\n]+', ' ', self._lecture_document_name() or 'Watermelon').strip()[:60] or 'Watermelon'
		self._pictures_insert_at = at
		self.courseware.export_pictures(self._courseware_note_folder(), name, paths)

	def _on_courseware_pictures(self, ok, copies):
		if copies and not self.bottom.isReadOnly():
			cursor = self.bottom.textCursor()
			at = getattr(self, '_pictures_insert_at', None)
			self._pictures_insert_at = None
			if at is None:
				cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.End)
			else:
				cursor.setPosition(max(0, min(int(at), len(self.bottom.toPlainText()))))
			self.bottom.setTextCursor(cursor)
			self.insert_files_as_attachments(copies)
		if not ok:
			watermelon_alert(self, _tr("Couldn't add the screenshots"), _tr('The screenshots are kept. Please try again.'))
		elif copies:
			self._show_mode_toast(_tr('Added to the note'))

	def _make_courseware_pdf_of(self, paths, into_path=''):
		into = next((item for item in self._note_pdfs() if item['path'] == into_path), None) if into_path else None
		self._save_courseware_pdf(into, list(paths))

	def _save_courseware_pdf(self, into=None, paths=None):
		"""截图合成一份 PDF 存进这张笔记；into = 笔记里已有的一份 PDF（截图加在它后面）；paths = 只这几张
		（列表里选中的），没有 = 全部。做好后用掉的截图离开列表，别的留着。"""
		if not self.courseware.shots or self.bottom.isReadOnly():
			return
		self._courseware_pdf_paths = paths
		if into is not None and not self.notes_mode_enabled:
			target = into['path']                          # 本地文件：直接加在原来那份后面
		else:
			if self.notes_mode_enabled:
				folder = os.path.join(WATERMELON_CACHE_ROOT, 'Lecture', 'Courseware', 'pdf')
			else:
				folder = self._attachment_base_dir() or WATERMELON_DATA_DIR
			name = re.sub(r'[\\/:*?"<>|\n]+', ' ', self._lecture_document_name() or 'Watermelon').strip()[:60] or 'Watermelon'
			if into is not None:
				stem = os.path.splitext(os.path.basename(into['path']))[0]
				target = os.path.join(folder, '%s %s.pdf' % (stem, datetime.now().strftime('%H%M%S')))
			else:
				target = os.path.join(folder, '%s slides %s.pdf' % (name, datetime.now().strftime('%Y-%m-%d %H%M%S')))
		self._show_mode_toast(_tr('Making the PDF…'))
		self.courseware.make_pdf(target, into['path'] if into is not None else '', getattr(self, '_courseware_pdf_paths', None))

	def _on_courseware_pdf(self, ok, target, existing):
		if not ok:
			watermelon_alert(self, _tr("Couldn't make the PDF"), _tr('The screenshots are kept. Please try again.'))
			return
		for window in list(self._attachment_previews):
			if existing and window.path == existing:
				window.close()                             # 这份 PDF 变了：开着的小窗关掉，再点开就是新的
		if not existing:
			cursor = self.bottom.textCursor()
			cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.End)
			self.bottom.setTextCursor(cursor)
			self.insert_files_as_attachments([target])
		elif target != existing:
			text = self.bottom.toPlainText()               # 备忘录里的附件：换成加了页的那一份
			for item in self._note_pdfs():
				if item['path'] == existing:
					end = text.find(')', item['offset'])
					if end > 0:
						cursor = self.bottom.textCursor()
						cursor.setPosition(item['offset'])
						cursor.setPosition(end + 1, PyQt6.QtGui.QTextCursor.MoveMode.KeepAnchor)
						cursor.insertText(watermelon_attachments.markdown_reference(target).strip())
					break
		else:
			watermelon_attachments._THUMBS.clear()
		self._show_mode_toast(_tr('Saved as PDF'))      # 用掉的截图课件那边已经拿走了，别的留着

	def _ask_courseware_end(self):
		"""听课结束时还有没存的截图：问一下怎么办。"""
		count = len(self.courseware.shots) if self.courseware is not None else 0
		if not count:
			return
		save, later, discard = _tr('Save as PDF'), _tr('Keep for Later'), _tr('Discard')
		answer = watermelon_choice(self, _tr('Save the screenshots into this note?'),
								   _tr('%d screenshots were taken as course material. They can be saved into the note as one PDF.') % count,
								   [discard, later, save], default=save, escape=later)
		if answer == save:
			self._save_courseware_pdf()
		elif answer == discard:
			self.courseware.discard()

	def toggle_lecture_mode(self):
		"""听课模式的开关（菜单栏图标菜单里的「🎓 Lecture Mode」）：开着时把此刻的内容 + 正在看的那一页课件发给 Broccoli
		总结成卡片；Broccoli 开着语音输入时，听到的话是第二条线。打开时右边的卡片面板一起拉出来；面板可以单独用
		右边的把手收回 / 拉出，不影响听课模式。"""
		self._ensure_lecture()
		self.lecture_mode_enabled = not self.lecture_mode_enabled
		lecture_action.setChecked(self.lecture_mode_enabled)
		if self.lecture_mode_enabled:
			missing = not watermelon_broccoli.broccoli_installed()
			self.lecture_session.start(self._lecture_document_name(), broccoli_missing=missing)
			if missing:     # 截图、拍照、合成 PDF、批注卡片照常；做卡片的那部分停着，不去一遍遍找 Broccoli
				QTimer.singleShot(0, lambda: self._broccoli_ready(_tr('Making cards from pages, speech and notes')))
			self._set_panel_open(True)
			if self._lecture_page() is not None:
				self.lecture_session.page_turned()
			self._show_mode_toast(_tr('Lecture Mode'))
		else:
			self.lecture_session.stop()
			self._sync_lecture_panel()
			self._show_mode_toast(_tr('Lecture Mode Off'))
			# 没放进笔记的截图不再问、不再丢：留在这张笔记的列表里，重启后也在（Ryan 2026-11-24：“只有你自己删才会删”）

	def _lecture_note_text(self):
		"""发给 Broccoli 当材料的文字：笔记正文；网页模式 = 网页上选中的字；Office 文件 = 那份文件里的字。"""
		if self.web_mode_enabled:
			return self._web_selected_text.replace('\u2029', '\n')
		if self._office_shown():
			return watermelon_marks.office_plain_text(self._current_local_file_path() or '')
		return self.bottom.toPlainText()

	def _lecture_focus(self):
		"""此刻在写的地方：光标所在的那一段，和它上面的各级标题（只用来告诉模型在哪，不让它去解释）。"""
		if self.web_mode_enabled:
			return {'current': self._web_selected_text.replace('\u2029', '\n'), 'outline': ''}
		if self._office_shown():
			return {'current': '', 'outline': os.path.basename(self._current_local_file_path() or '')}
		cursor = self.bottom.textCursor()
		block = cursor.block()
		current = [block.text()]
		before = block.previous()
		while before.isValid() and before.text().strip() and len('\n'.join(current)) < 600:
			current.insert(0, before.text())        # 同一段里光标上面的几行
			before = before.previous()
		trail = {}
		for _line, level, text in watermelon_outline.headings_in(self.bottom.toPlainText()):
			if _line > block.blockNumber():
				break
			trail = {k: v for k, v in trail.items() if k < level}
			trail[level] = text
		return {'current': '\n'.join(current).strip(), 'outline': ' > '.join(trail[k] for k in sorted(trail))}

	def ask_broccoli(self):
		"""编辑框右键「Ask Broccoli…」：一个小对话框写问题；选了字就是问这段字。"""
		selected = self.bottom.textCursor().selectedText().replace('\u2029', '\n').strip()
		return self._open_ask_dialog(selected)

	def _open_ask_dialog(self, about=''):
		"""问 Broccoli 的小对话框（只从右键菜单打开：卡片的、编辑框的）。问了以后右边面板拉出来，回答是里面的一张卡片。
		2026-11-21 Ryan：“右侧底下的 ask 就去掉吧，能右键菜单就不要再多加入口了”。"""
		if not self._broccoli_ready(_tr('Asking a question')):
			return None
		self._ensure_lecture()
		if getattr(self, '_ask_dialog', None) is not None:
			self._ask_dialog.close()
		dialog = watermelon_lecture.AskDialog(about)
		dialog.asked.connect(lambda question, what: (self._set_panel_open(True), self.lecture_session.ask(question, what)))
		dialog.destroyed.connect(lambda *_a: setattr(self, '_ask_dialog', None))
		self._ask_dialog = dialog
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		return dialog

	def _broccoli_ready(self, what):
		"""Broccoli 在这台 Mac 上吗（同 Tomato：看它的数据文件夹，或系统认不认得这个程序）。不在：这次运行第一次
		用到时先推荐下载（系统提醒，默认按钮 = 下载），之后只出一行提示。入口不藏不灰（同 Tomato）。
		Ryan 2026-11-21：“学习一下 tomato 的处理，如果用户电脑上没有 broccoli 怎么办”“先推荐下载”。"""
		if watermelon_broccoli.broccoli_installed():
			return True
		if getattr(self, '_broccoli_missing_told', False):
			self._show_mode_toast(_tr('Needs Broccoli'))
			return False
		self._broccoli_missing_told = True
		download, later = _tr('Download Broccoli…'), _tr('Not Now')
		answer = watermelon_choice(self, _tr('Broccoli is not on this Mac'),
								   _tr('%s is done by Broccoli, an AI assistant app for Mac. Download it, open it once, then try again.') % what,
								   [later, download], default=download, escape=later)
		if answer == download:
			threading.Thread(target=watermelon_broccoli.open_download_page, daemon=True).start()
		return False

	def _set_panel_open(self, on):
		on = bool(on)
		if on != self._panel_open:
			self._panel_open = on
			_write_switch('side_panel.txt', on)
		if on:
			self._ensure_lecture()
			self.side_handles.set_attention('right', False)      # 拉出来就算看过了：把手上的小圆点去掉
		self._sync_lecture_panel()

	def _place_lecture_panel(self, screen_height):
		"""编辑区右边那一条：和左边的附件列表对称，宽度固定，不盖到编辑区。"""
		panel = getattr(self, 'lecture_panel', None)
		if panel is None:
			return
		panel.move(1378 + 8, 12)               # 右边空条 1378–1520：离编辑区 8、离窗口边 8，刚好填满，不压到编辑区
		panel.setFixedHeight(max(160, int(screen_height) - 310))

	def _sync_lecture_panel(self):
		"""被把手拉出来了、而且中间那一列在显示（笔记、网页、Office 文件都算）时才出现。"""
		if getattr(self, 'lecture_panel', None) is None and self._panel_open and self._hit_mask_ready and not self._side_column_rect().isEmpty():
			self._ensure_lecture()           # 上次退出时面板是拉出来的
		panel = getattr(self, 'lecture_panel', None)
		if getattr(self, 'side_handles', None) is not None:
			self.side_handles.sync_attention()
		if panel is None:
			return
		wanted = self._panel_open and not self._side_column_rect().isEmpty()
		if wanted != panel.isVisible():
			panel.setVisible(wanted)
			if wanted:
				panel.raise_()
			if self._hit_mask_ready:
				QTimer.singleShot(0, self._update_hit_mask)

	def _lecture_page(self):
		"""此刻正在看的那一页课件：{label, image, key}；没有 = None（那就只发笔记）。"""
		source = self._lecture_page_source
		if isinstance(source, dict):                       # 一张当课件用的截图
			image = QImage(source.get('path', ''))
			if not image.isNull():
				return {'label': source.get('label', ''), 'image': image, 'key': source.get('path')}
		window = source if source in self._attachment_previews else (self._attachment_previews[-1] if self._attachment_previews else None)
		if window is None or window.kind not in ('pdf', 'image'):
			return None
		image = window.current_page_image()
		if image.isNull():
			return None
		name = os.path.basename(window.path)
		label = '%s p.%d' % (name, window.current_page() + 1) if window.kind == 'pdf' else name
		return {'label': label, 'image': image, 'key': (window.path, window.current_page() if window.kind == 'pdf' else 0)}

	def _on_preview_page_changed(self, window):
		self._lecture_page_source = window
		if self.lecture_mode_enabled and self.lecture_session is not None:
			self.lecture_session.page_turned()

	def _insert_lecture_card(self, markdown_text):
		"""把一张卡片作为一个信息块加进正文（光标所在的那一段后面）。"""
		if self.bottom.isReadOnly() or not markdown_text:
			return
		cursor = self.bottom.textCursor()
		cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.EndOfBlock)
		before = cursor.block().text().strip()
		cursor.insertText(('\n\n' if before else '') + markdown_text + '\n\n')
		self.bottom.setTextCursor(cursor)

	def _clear_lecture_archive(self):
		count = len(self.lecture_session.store.archived())
		if not count:
			return
		answer = watermelon_choice(self, _tr('Clear all archived cards?'),
								   _tr('%d archived cards will be deleted. This cannot be undone.') % count,
								   [_tr('Cancel'), _tr('Clear All')], default=_tr('Cancel'), escape=_tr('Cancel'))
		if answer == _tr('Clear All'):
			self.lecture_session.store.clear_archived()
			self.lecture_panel.refresh('')

	def _lecture_stop_before_quit(self):
		if self.lecture_session is not None and self.lecture_mode_enabled:
			self.lecture_session.stop()

	def open_attachment_preview(self, item):
		"""在一个独立的小窗里预览这个附件；同一个文件已经开着就把那个窗口拿到前面。可以同时开很多个。"""
		for window in self._attachment_previews:
			if window.path == item['path']:
				window.show()
				window.raise_()
				window.activateWindow()
				return window
		window = watermelon_attachments.AttachmentPreviewWindow(item)
		window.open_in_editor.connect(self._open_attachment_in_editor)
		window.page_changed.connect(lambda _path, _page, w=window: self._on_preview_page_changed(w))
		window.closed.connect(lambda w: self._attachment_previews.remove(w) if w in self._attachment_previews else None)
		# 每开一个往右下错开一点，不叠在一起
		start = self.mapToGlobal(QPoint(150, 60))
		step = 28 * (len(self._attachment_previews) % 8)
		window.move(start.x() + step, start.y() + step)
		self._attachment_previews.append(window)
		window.show()
		window.raise_()
		window.activateWindow()
		self._on_preview_page_changed(window)
		return window

	def _open_attachment_in_editor(self, path):
		"""预览小窗里的“Open in Editor”：Word / Excel / PowerPoint 在编辑区那一列打开（本地模式的 Office 文件）。"""
		if self.web_mode_enabled:
			self.toggle_web_mode()
		if self.notes_mode_enabled:
			self.toggle_notes_mode()
		self._open_office_file(path)

	def _show_attachment_in_text(self, item):
		if int(item.get('offset', 0)) < 0:
			return      # 一张还没存进笔记的截图：正文里没有它
		cursor = self.bottom.textCursor()
		cursor.setPosition(min(int(item.get('offset', 0)), len(self.bottom.toPlainText())))
		self.bottom.setTextCursor(cursor)
		self.bottom.ensureCursorVisible()
		self.bottom.setFocus()

	def _watch_page_drops(self):
		"""排好版的页面（网页视图）真正收拖放的是它里面后来加进来的那个子部件：找到它，盯住它的拖放。"""
		target = self.topleft.focusProxy() if hasattr(self, 'topleft') else None
		if target is not None and target is not self._page_drop_target:
			target.installEventFilter(self)
			self._page_drop_target = target

	def _attachment_removable(self, item):
		if item.get('courseware'):
			return self.courseware is not None
		return not self.bottom.isReadOnly() and not self.web_mode_enabled and not self._office_shown()

	def _remove_attachment(self, item):
		"""左边列表右键的删除（Ryan 2026-11-24：“没有删除的地方”）：课件截图 = 连文件一起删；
		正文里的附件 = 只删正文里引用它的那一行（⌘Z 能撤回），文件本身不动。"""
		if item.get('courseware'):
			if self.courseware is not None:
				self.courseware.remove(item.get('path', ''))
			return
		if not self._attachment_removable(item):
			return
		span = watermelon_attachments.reference_span(self.bottom.toPlainText(), item, self._attachment_base_dir())
		if span is None:
			self._refresh_attachment_rail()      # 正文刚改过：列表重新对一遍
			return
		cursor = self.bottom.textCursor()
		cursor.setPosition(span[0])
		cursor.setPosition(span[1], PyQt6.QtGui.QTextCursor.MoveMode.KeepAnchor)
		cursor.removeSelectedText()             # 走编辑框自己的撤销
		self.bottom.setTextCursor(cursor)

	def insert_files_as_attachments(self, paths):
		"""把文件加进正文（光标所在的位置，各占一段）：图片 = ![名字](文件)，别的 = [名字](文件)。"""
		if self.bottom.isReadOnly() or self.web_mode_enabled or self._office_shown():
			return
		references = [watermelon_attachments.markdown_reference(path) for path in paths if os.path.isfile(path)]
		if not references:
			return
		cursor = self.bottom.textCursor()
		cursor.movePosition(PyQt6.QtGui.QTextCursor.MoveOperation.EndOfBlock)
		before = cursor.block().text().strip()
		cursor.insertText(('\n\n' if before else '') + '\n\n'.join(references) + '\n\n')
		self.bottom.setTextCursor(cursor)

	def _connect_screen_signals(self):
		if self._screen_signals_connected:
			return
		self._screen_signals_connected = True
		window_handle = self.windowHandle()
		if window_handle:
			window_handle.screenChanged.connect(self._on_window_screen_changed)
			self._attach_screen_geometry_signals(window_handle.screen())
		app_obj = QGuiApplication.instance()
		if app_obj:
			app_obj.screenAdded.connect(self._on_screens_changed)
			app_obj.screenRemoved.connect(self._on_screens_changed)
			app_obj.primaryScreenChanged.connect(self._on_primary_screen_changed)

	def _attach_screen_geometry_signals(self, screen):
		if not screen or screen == self._tracked_screen:
			return
		if self._tracked_screen:
			try:
				self._tracked_screen.availableGeometryChanged.disconnect(self._on_screen_geometry_changed)
			except Exception:
				pass
			try:
				self._tracked_screen.geometryChanged.disconnect(self._on_screen_geometry_changed)
			except Exception:
				pass
		self._tracked_screen = screen
		screen.availableGeometryChanged.connect(self._on_screen_geometry_changed)
		screen.geometryChanged.connect(self._on_screen_geometry_changed)

	def _on_window_screen_changed(self, screen):
		self._attach_screen_geometry_signals(screen)
		if screen:
			self._apply_screen_geometry(screen.availableGeometry())

	def _on_primary_screen_changed(self, screen):
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			return
		if screen:
			self._apply_screen_geometry(screen.availableGeometry())

	def _on_screens_changed(self, _screen):
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			self._attach_screen_geometry_signals(window_handle.screen())
			self._apply_screen_geometry(window_handle.screen().availableGeometry())

	def _on_screen_geometry_changed(self, _rect):
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			self._apply_screen_geometry(window_handle.screen().availableGeometry())

	def _apply_screen_geometry(self, screen_geom):
		screen_width = int(screen_geom.width())
		screen_height = int(screen_geom.height())
		screen_x = int(screen_geom.x())
		screen_y = int(screen_geom.y())
		if self.qw0.isVisible():
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(1520, screen_height)
			self._adjust_components_for_screen(screen_height)
			x_center = screen_x + int(screen_width / 2) - 760
			self.move(x_center, screen_y)
			return
		self.setFixedSize(100, 10)
		x_center = screen_x + int(screen_width / 2) - 50
		self.move(x_center, screen_y)

	def _current_screen_geometry(self):
		"""获取当前鼠标所在屏幕的几何信息，用于多显示器支持"""
		screen = QGuiApplication.screenAt(QCursor.pos())
		if screen:
			return screen.availableGeometry()
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			return window_handle.screen().availableGeometry()
		if self.screen():
			return self.screen().availableGeometry()
		primary = QGuiApplication.primaryScreen()
		return primary.availableGeometry() if primary else QRect(0, 0, 1440, 900)

	def _adjust_components_for_screen(self, screen_height):
		"""根据屏幕高度调整内部组件的尺寸和位置"""
		# 调整顶部文本编辑器的最大高度
		self.topleft.setMaximumHeight(screen_height - 200)
		self.topleft_frame.setMaximumHeight(screen_height - 200)
		self.topright.setMaximumHeight(screen_height - 200)
		# 调整主内容区域的高度
		self.qw0.setFixedHeight(screen_height - 118)
		# 调整分割器的尺寸
		self._apply_splitter2_ratio(screen_height)
		# 调整底部图片的位置
		self.l1.move(0, screen_height - 215)
		# 调整蓝色按钮的位置
		self.btn_00.move(160+37+12, screen_height - 35)
		# 调整设置按钮的位置
		# self.btn0_1.move(35, screen_height - 185)
		# self.btn0_2.move(1435, screen_height - 182)
		self.btn0_1.move(158, screen_height - 70)
		self.btn0_2.move(1324, screen_height - 70)
		self.btn0_sound.move(1383, screen_height - 200)
		self.btn0_tp.move(1383, screen_height - 150)
		self.btn0_web.move(1383, screen_height - 100)
		self._place_attachment_rail(screen_height)
		self._position_word_count_label()

	def _count_visible_chars(self, text):
		if not text:
			return 0
		normalized = text.replace('\u2029', '\n')
		return len(normalized)

	def _count_words(self, text):
		if not text:
			return 0
		normalized = text.replace('\u2029', '\n')
		# Count each Chinese character as one word-like token.
		cjk_count = len(re.findall(r'[\u4e00-\u9fff]', normalized))
		latin_words = len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", normalized))
		number_words = len(re.findall(r"\d+(?:[.,]\d+)?", normalized))
		return cjk_count + latin_words + number_words

	def _position_word_count_label(self):
		if not hasattr(self, "word_count_label") or not hasattr(self, "btn0_1"):
			return
		x = self.btn0_1.x() - 10
		SCREEN_HEIGHT = int(self.screen().availableGeometry().height())
		# y = self.btn0_1.y() + max(0, (self.btn0_1.height() - self.word_count_label.height()) // 2)
		self.word_count_label.move(x, SCREEN_HEIGHT - 112)

	def _has_active_document_for_word_count(self):
		if self.web_mode_enabled:
			return bool(self._web_selected_text.strip())
		if self._office_shown():
			return False   # Office 组件有自己的字数统计
		if self.notes_mode_enabled:
			if not getattr(self, "notes_active", False):
				return False
			if not getattr(self, "notes_current_title", None):
				return False
			if hasattr(self, "widget_notes") and self.widget_notes.currentIndex() < 0:
				return False
			return True
		if not hasattr(self, "widget0"):
			return False
		if self.widget0.count() <= 0 or self.widget0.currentIndex() < 0:
			return False
		return True

	def _notes_state_text(self):
		if not self.notes_mode_enabled or self.web_mode_enabled or not self.notes_active:
			return ''
		if self._notes_save_state == 'saving':
			return _tr('Saving…')
		if self._notes_save_state == 'failed':
			return _tr('Not saved')
		if self.notes_dirty:
			return _tr('Edited')
		return _tr('Saved') if self._notes_save_state == 'saved' else ''

	def _update_word_count_label(self):
		"""字数那一行；备忘录模式下末尾带保存状态（Saved / Saving… / Edited / Not saved，没存上是红字）。"""
		self._update_word_count_label_only()
		state = self._notes_state_text() if hasattr(self, '_notes_save_state') else ''
		failed = bool(state) and self._notes_save_state == 'failed'
		if failed != getattr(self, '_word_count_label_red', False):
			self._word_count_label_red = failed
			self.word_count_label.setStyleSheet(self.word_count_label.styleSheet().replace(
				'color: #FFFFFF;' if failed else 'color: #FF6B6B;', 'color: #FF6B6B;' if failed else 'color: #FFFFFF;'))
		if state and hasattr(self, 'word_count_label'):
			shown = self.word_count_label.text() if self.word_count_label.isVisible() else ''
			self.word_count_label.setText((shown + '  ·  ' + state) if shown else state)
			self.word_count_label.adjustSize()
			self._position_word_count_label()
			self.word_count_label.setVisible(self.btn0_1.isVisible())

	def _update_word_count_label_only(self):
		if not hasattr(self, "bottom") or not hasattr(self, "word_count_label"):
			return
		if not self._has_active_document_for_word_count():
			self.word_count_label.hide()
			return
		if self.web_mode_enabled:
			# 网页模式：只统计网页里选中的文字
			selected_text = self._web_selected_text.replace('\u2029', '\n')
			self.word_count_label.setText(
				_tr("Selected: %1 chars, %2 words").replace('%1', str(self._count_visible_chars(selected_text))).replace('%2', str(self._count_words(selected_text)))
			)
			self.word_count_label.adjustSize()
			self._position_word_count_label()
			self.word_count_label.setVisible(self.btn0_1.isVisible())
			return
		full_text = self.bottom.toPlainText()
		total_chars = self._count_visible_chars(full_text)
		if total_chars <= 0:
			self.word_count_label.hide()
			return
		total_words = self._count_words(full_text)
		selected_text = self.bottom.textCursor().selectedText().replace('\u2029', '\n')
		selected_chars = self._count_visible_chars(selected_text)
		if selected_chars > 0:
			selected_words = self._count_words(selected_text)
			self.word_count_label.setText(
				_tr("Selected: %1 chars, %2 words | Total: %3 chars, %4 words").replace('%1', str(selected_chars)).replace(
					'%2', str(selected_words)).replace('%3', str(total_chars)).replace('%4', str(total_words))
			)
		else:
			self.word_count_label.setText(_tr("Total: %1 chars, %2 words").replace('%1', str(total_chars)).replace('%2', str(total_words)))
		self.word_count_label.adjustSize()
		self._position_word_count_label()
		if self.btn0_1.isVisible():
			self.word_count_label.show()
		else:
			self.word_count_label.hide()

	def _default_splitter2_ratio(self, screen_height):
		total = max(screen_height - 100, 1)
		return (screen_height - 200) / total

	def _apply_splitter2_ratio(self, screen_height):
		if self._splitter2_ratio is None:
			self._splitter2_ratio = self._default_splitter2_ratio(screen_height)
		ratio = self._splitter2_ratio if self._splitter2_user_set else self._default_splitter2_ratio(screen_height)
		ratio = min(max(ratio, 0.05), 0.95)
		top = int(1000 * ratio)
		bottom = max(1, 1000 - top)
		self.splitter2.setSizes([top, bottom])

	def _load_always_on_top(self):
		try:
			value = codecs.open(SettingsPath + 'always_on_top.txt', 'r', encoding='utf-8').read().strip()
			return value != '0'
		except Exception:
			return True

	def _apply_window_flags(self):
		flags = Qt.WindowType.FramelessWindowHint
		if self._always_on_top:
			flags |= Qt.WindowType.WindowStaysOnTopHint
		self.setWindowFlags(flags)

	def _current_window_screen_geometry(self):
		window_handle = self.windowHandle()
		if window_handle and window_handle.screen():
			return window_handle.screen().availableGeometry()
		return self._current_screen_geometry()

	def set_always_on_top(self, enabled):
		was_visible = self.isVisible()
		screen_geom = self._current_window_screen_geometry()
		self._always_on_top = bool(enabled)
		self._apply_window_flags()
		if was_visible:
			self.show()
			self.raise_()
			if self._always_on_top:
				self.activateWindow()
			self._apply_screen_geometry(screen_geom)
		try:
			with open(SettingsPath + 'always_on_top.txt', 'w', encoding='utf-8') as f0:
				f0.write('1' if self._always_on_top else '0')
		except Exception:
			pass

	def is_always_on_top(self):
		return self._always_on_top

	def set_bg_color(self, bg_color):
		# 保存当前背景颜色
		self._current_bg_color = bg_color
		# 根据暗色/亮色模式设置文字颜色
		text_color = '#FFFFFF' if is_dark_theme(app) else '#000000'
		border_color = '#555555' if is_dark_theme(app) else 'grey'
		# 更新 topleft (QWebEngineView) 的背景颜色
		self.topleft.setStyleSheet(f"border: 0px; background: {bg_color};")
		self.topleft.page().setBackgroundColor(QColor(bg_color))
		# 更新 topleft_frame (QFrame#webFrame) 的背景颜色
		self.topleft_frame.setStyleSheet(f'''
			QFrame#webFrame{{
				border: 1px solid {border_color};
				border-radius:4px;
				padding: 0px;
				background-clip: border;
				background-color: {bg_color};
			}}
		''')
		# 更新 topright (QTextEdit) 的背景颜色
		self.topright.setStyleSheet(f'''
			QTextEdit{{
				border: 1px solid {border_color};
				border-radius:4px;
				padding: 1px 5px 1px 3px;
				background-clip: border;
				background-color: {bg_color};
				color: {text_color};
			}}
		''')
		# 更新 bottom (QTextEdit) 的背景颜色
		self.bottom.setStyleSheet(f'''
			QTextEdit{{
				border: 1px solid {border_color};
				border-radius:4px;
				padding: 1px 5px 1px 3px;
				background-clip: border;
				background-color: {bg_color};
				color: {text_color};
			}}
		''')
		# 重新渲染 topleft 和 topright 的 HTML 内容以应用新的背景颜色
		try:
			previewtext = self.bottom.toPlainText()
			self._request_async_preview_render(previewtext, debounce_ms=0)
		except Exception:
			pass

	def move_window(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		animation.setDuration(250)
		new_pos = QRect(width, height, self.width(), self.height())
		animation.setEndValue(new_pos)
		self._watch_slide_landing(animation, new_pos)
		animation.start()
		self.i += 1

	# Stage Manager (2026-11-25; measured on the real screen in the sister app with the same edge panel: while
	# the window slid out the system fitted it into the room beside its strip — moved and made smaller — and
	# the app never heard of it). Once a slide has settled: is the window where it was sent? Put back once
	# per slide, so nothing is fought over.
	SLIDE_LANDING_CHECK_MS = 450
	SLIDE_LANDING_TOLERANCE = 8

	def _watch_slide_landing(self, animation, wanted):
		self._slide_serial = getattr(self, '_slide_serial', 0) + 1
		serial = self._slide_serial
		wanted = QRect(wanted)
		animation.finished.connect(lambda: QTimer.singleShot(self.SLIDE_LANDING_CHECK_MS, lambda: self._check_slide_landing(serial, QRect(wanted))))

	def _slide_landing_off(self, got, wanted):
		"""Away from where it was sent: the left edge elsewhere, or made SMALLER. (Wider / taller than asked is
		the window's own smallest size on a small screen, not somebody moving it.)"""
		tolerance = self.SLIDE_LANDING_TOLERANCE
		return (abs(got.x() - wanted.x()) > tolerance or got.width() < wanted.width() - tolerance
				or got.height() < wanted.height() - tolerance)

	def _check_slide_landing(self, serial, wanted):
		if serial != getattr(self, '_slide_serial', 0) or not self.isVisible():
			return 'stale'
		got = self.geometry()
		if not self._slide_landing_off(got, wanted):
			return 'in place'
		logging.info('Main window was moved after its slide: wanted %dx%d at (%d,%d), found %dx%d at (%d,%d) -> put back once',
					 wanted.width(), wanted.height(), wanted.x(), wanted.y(), got.width(), got.height(), got.x(), got.y())
		self.setGeometry(QRect(wanted))
		self._slide_put_back = getattr(self, '_slide_put_back', 0) + 1
		QTimer.singleShot(700, lambda: self._log_slide_landing(serial, QRect(wanted)))
		return 'put back'

	def _log_slide_landing(self, serial, wanted):
		if serial != getattr(self, '_slide_serial', 0) or not self.isVisible():
			return
		got = self.geometry()
		logging.info('Main window after being put back: %dx%d at (%d,%d) — %s', got.width(), got.height(), got.x(), got.y(),
					 'moved again (left as it is)' if self._slide_landing_off(got, wanted) else 'stayed')

	def move_window2(self, width, height):
		animation = QPropertyAnimation(self, b"geometry", self)
		animation.setDuration(1000)
		new_pos = QRect(width, height, self.width(), self.height())
		animation.setEndValue(new_pos)
		animation.start()
		self.i += 1

	def _start_intro_animation(self):
		"""启动动画：splitter2从上到下，l1从下到上，然后qw1和按钮淡入"""
		# 保存目标位置
		qw0_target_y = self.qw0.y()
		l1_target_y = self.l1.y()

		# 设置初始位置（splitter2/qw0 在上方，l1 在下方）
		self.qw0.move(self.qw0.x(), -self.qw0.height())
		self.l1.move(self.l1.x(), self.height() + 50)

		# 先隐藏需要淡入的组件
		self.qw1.setVisible(False)
		self.btn_00.setVisible(False)
		self.btn0_1.setVisible(False)
		self.btn0_2.setVisible(False)
		self.btn0_sound.setVisible(False)
		self.btn0_tp.setVisible(False)
		self.btn0_web.setVisible(False)
		self.word_count_label.setVisible(False)

		# 创建 qw0 从上到下的动画
		self._anim_qw0 = QPropertyAnimation(self.qw0, b"pos", self)
		self._anim_qw0.setDuration(600)
		self._anim_qw0.setStartValue(self.qw0.pos())
		self._anim_qw0.setEndValue(self.qw0.pos().__class__(self.qw0.x(), qw0_target_y))
		self._anim_qw0.setEasingCurve(QEasingCurve.Type.OutCubic)

		# 创建 l1 从下到上的动画
		self._anim_l1 = QPropertyAnimation(self.l1, b"pos", self)
		self._anim_l1.setDuration(600)
		self._anim_l1.setStartValue(self.l1.pos())
		self._anim_l1.setEndValue(self.l1.pos().__class__(self.l1.x(), l1_target_y))
		self._anim_l1.setEasingCurve(QEasingCurve.Type.OutCubic)

		# 并行执行两个滑动动画
		self._slide_group = QParallelAnimationGroup(self)
		self._slide_group.addAnimation(self._anim_qw0)
		self._slide_group.addAnimation(self._anim_l1)
		self._slide_group.finished.connect(self._start_fade_in_animation)
		self._slide_group.start()

	def _start_fade_in_animation(self):
		"""滑动动画完成后，开始淡入动画"""
		# 为每个需要淡入的组件创建透明度效果
		self._opacity_effects = []
		self._fade_animations = []
		fade_widgets = [self.qw1, self.btn_00, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web, self.word_count_label]

		self._fade_group = QParallelAnimationGroup(self)

		for widget in fade_widgets:
			# 创建透明度效果
			opacity_effect = QGraphicsOpacityEffect(widget)
			opacity_effect.setOpacity(0.0)
			widget.setGraphicsEffect(opacity_effect)
			widget.setVisible(True)
			self._opacity_effects.append(opacity_effect)

			# 创建淡入动画
			fade_anim = QPropertyAnimation(opacity_effect, b"opacity", self)
			fade_anim.setDuration(400)
			fade_anim.setStartValue(0.0)
			fade_anim.setEndValue(1.0)
			fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
			self._fade_animations.append(fade_anim)
			self._fade_group.addAnimation(fade_anim)

		glass_kit.resync_inwindow_glass(self)   # 淡入这段由 Qt 画圆片（玻璃不会跟着变淡）
		self._fade_group.finished.connect(self._on_intro_animation_finished)
		self._fade_group.start()

	def _on_intro_animation_finished(self):
		"""启动动画完成后的清理工作"""
		# 移除透明度效果，恢复正常渲染
		for widget in [self.qw1, self.btn_00, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web, self.word_count_label]:
			widget.setGraphicsEffect(None)
		glass_kit.resync_inwindow_glass(self)   # 淡入时圆按钮由 Qt 画，淡完换回系统玻璃
		# 清理动画对象引用
		self._opacity_effects = []
		self._fade_animations = []
		self._update_word_count_label()

	def _start_pin_show_animation(self, screen_height):
		"""pin_a_tab 显示时的动画：btn_00 下落到屏幕外，然后是标准启动动画"""
		# 保存 btn_00 的目标位置和尺寸
		btn_00_target_x = 160 + 37 + 12
		btn_00_target_y = screen_height - 35
		btn_00_target_width = 1200 - 74 - 24
		btn_00_target_height = 10

		# 设置 btn_00 的初始状态：目标尺寸，在上方
		initial_y = -50  # 从屏幕上方开始

		self.btn_00.setFixedSize(btn_00_target_width, btn_00_target_height)
		self.btn_00.move(btn_00_target_x, initial_y)
		self.btn_00.setVisible(True)
		self.btn_00.raise_()

		# 隐藏其他组件，等待后续动画
		self.qw0.setVisible(False)
		self.qw1.setVisible(False)
		self.l1.setVisible(False)
		self.btn0_1.setVisible(False)
		self.btn0_2.setVisible(False)
		self.btn0_sound.setVisible(False)
		self.btn0_tp.setVisible(False)
		self.btn0_web.setVisible(False)
		self.word_count_label.setVisible(False)

		# 保存目标值供动画使用
		self._btn_00_target_x = btn_00_target_x
		self._btn_00_target_y = btn_00_target_y
		self._btn_00_target_width = btn_00_target_width
		self._btn_00_target_height = btn_00_target_height
		self._pin_screen_height = screen_height

		# 创建位置动画（从上到下，落到屏幕外）
		self._anim_btn_00_pos = QPropertyAnimation(self.btn_00, b"pos", self)
		self._anim_btn_00_pos.setDuration(350)  # 稍长一点让动画更流畅
		self._anim_btn_00_pos.setStartValue(self.btn_00.pos())
		# 落到屏幕下方（屏幕高度 + 50，确保看不到）
		self._anim_btn_00_pos.setEndValue(self.btn_00.pos().__class__(btn_00_target_x, screen_height + 50))
		self._anim_btn_00_pos.setEasingCurve(QEasingCurve.Type.InQuad)  # 加速下落效果

		# 只执行位置动画
		self._anim_btn_00_pos.finished.connect(self._on_btn_00_anim_finished)
		self._anim_btn_00_pos.start()

	def _on_btn_00_anim_finished(self):
		"""btn_00 动画完成后，隐藏它并开始标准启动动画"""
		# 隐藏 btn_00，它将在后续淡入动画中重新显示
		self.btn_00.setVisible(False)

		# 将 btn_00 移动到最终应该出现的位置（为后续淡入做准备）
		self.btn_00.setFixedSize(self._btn_00_target_width, self._btn_00_target_height)
		self.btn_00.move(self._btn_00_target_x, self._btn_00_target_y)

		screen_height = self._pin_screen_height
		# 先把 qw0 和 l1 移动到屏幕外，再显示，防止闪现
		self.qw0.move(self.qw0.x(), -self.qw0.height())
		self.l1.move(self.l1.x(), screen_height + 50)
		# 现在才显示（已经在屏幕外了）
		self.qw0.setVisible(True)
		self.l1.setVisible(True)

		# 开始标准启动动画（splitter 从上到下，l1 从下到上）
		self._start_intro_animation_for_pin()

	def _start_intro_animation_for_pin(self):
		"""pin_a_tab 专用的启动动画（不包含初始隐藏逻辑）"""
		screen_height = self._pin_screen_height

		# 保存目标位置
		qw0_target_y = 0  # qw0 的目标 Y 位置通常是 0
		l1_target_y = screen_height - 215

		# 设置初始位置
		self.qw0.move(self.qw0.x(), -self.qw0.height())
		self.l1.move(self.l1.x(), screen_height + 50)

		# 隐藏需要淡入的组件
		self.qw1.setVisible(False)
		self.btn_00.setVisible(False)
		self.btn0_1.setVisible(False)
		self.btn0_2.setVisible(False)
		self.btn0_sound.setVisible(False)
		self.btn0_tp.setVisible(False)
		self.btn0_web.setVisible(False)
		self.word_count_label.setVisible(False)

		# 创建 qw0 从上到下的动画
		self._anim_qw0 = QPropertyAnimation(self.qw0, b"pos", self)
		self._anim_qw0.setDuration(600)
		self._anim_qw0.setStartValue(self.qw0.pos())
		self._anim_qw0.setEndValue(self.qw0.pos().__class__(self.qw0.x(), qw0_target_y))
		self._anim_qw0.setEasingCurve(QEasingCurve.Type.OutCubic)

		# 创建 l1 从下到上的动画
		self._anim_l1 = QPropertyAnimation(self.l1, b"pos", self)
		self._anim_l1.setDuration(600)
		self._anim_l1.setStartValue(self.l1.pos())
		self._anim_l1.setEndValue(self.l1.pos().__class__(self.l1.x(), l1_target_y))
		self._anim_l1.setEasingCurve(QEasingCurve.Type.OutCubic)

		# 并行执行两个滑动动画
		self._slide_group = QParallelAnimationGroup(self)
		self._slide_group.addAnimation(self._anim_qw0)
		self._slide_group.addAnimation(self._anim_l1)
		self._slide_group.finished.connect(self._start_fade_in_animation)
		self._slide_group.start()

	def _start_pin_hide_animation(self, screen_height, callback):
		"""pin_a_tab 隐藏时的动画：所有组件同时退场"""
		self._pin_hide_callback = callback
		self._pin_hide_screen_height = screen_height

		# 确保清除之前可能残留的透明度效果
		self.btn_00.setGraphicsEffect(None)

		# 创建主动画组（所有动画同时进行）
		self._hide_anim_group = QParallelAnimationGroup(self)

		# 1. qw0 向上移出屏幕
		self._anim_qw0_hide = QPropertyAnimation(self.qw0, b"pos", self)
		self._anim_qw0_hide.setDuration(400)
		self._anim_qw0_hide.setStartValue(self.qw0.pos())
		self._anim_qw0_hide.setEndValue(self.qw0.pos().__class__(self.qw0.x(), -self.qw0.height()))
		self._anim_qw0_hide.setEasingCurve(QEasingCurve.Type.InCubic)
		self._hide_anim_group.addAnimation(self._anim_qw0_hide)

		# 2. l1 向下移出屏幕
		self._anim_l1_hide = QPropertyAnimation(self.l1, b"pos", self)
		self._anim_l1_hide.setDuration(400)
		self._anim_l1_hide.setStartValue(self.l1.pos())
		self._anim_l1_hide.setEndValue(self.l1.pos().__class__(self.l1.x(), screen_height + 50))
		self._anim_l1_hide.setEasingCurve(QEasingCurve.Type.InCubic)
		self._hide_anim_group.addAnimation(self._anim_l1_hide)

		# 3. 按钮组件淡出（包括 btn_00）
		self._hide_opacity_effects = []
		self._hide_fade_animations = []
		fade_widgets = [self.qw1, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web, self.btn_00, self.word_count_label]

		for widget in fade_widgets:
			opacity_effect = QGraphicsOpacityEffect(widget)
			opacity_effect.setOpacity(1.0)
			widget.setGraphicsEffect(opacity_effect)
			self._hide_opacity_effects.append(opacity_effect)

			fade_anim = QPropertyAnimation(opacity_effect, b"opacity", self)
			fade_anim.setDuration(400)
			fade_anim.setStartValue(1.0)
			fade_anim.setEndValue(0.0)
			fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)
			self._hide_fade_animations.append(fade_anim)
			self._hide_anim_group.addAnimation(fade_anim)

		glass_kit.resync_inwindow_glass(self)   # 系统玻璃不会跟着变淡：淡出这段由 Qt 画同样的圆片
		self._hide_anim_group.finished.connect(self._on_pin_hide_animation_finished)
		self._hide_anim_group.start()

	def _on_pin_hide_animation_finished(self):
		"""隐藏动画完成后的清理和回调"""
		# 移除透明度效果（包括 btn_00）
		for widget in [self.qw1, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn0_tp, self.btn0_web, self.btn_00, self.word_count_label]:
			widget.setGraphicsEffect(None)

		# 隐藏组件
		self.qw0.setVisible(False)
		self.qw1.setVisible(False)
		self.l1.setVisible(False)
		self.btn_00.setVisible(False)
		self.btn0_1.setVisible(False)
		self.btn0_sound.setVisible(False)
		self.btn0_tp.setVisible(False)
		self.btn0_web.setVisible(False)
		self.word_count_label.setVisible(False)

		# 清理
		self._hide_opacity_effects = []
		self._hide_fade_animations = []

		# 先执行回调（设置 btn_00 位置、窗口缩小移动）
		if self._pin_hide_callback:
			self._pin_hide_callback()

		# 回调执行后，btn_00 淡入显示
		self.btn_00.setVisible(True)
		self._btn_00_fadein_effect = QGraphicsOpacityEffect(self.btn_00)
		self._btn_00_fadein_effect.setOpacity(0.0)
		self.btn_00.setGraphicsEffect(self._btn_00_fadein_effect)

		self._btn_00_fadein_anim = QPropertyAnimation(self._btn_00_fadein_effect, b"opacity", self)
		self._btn_00_fadein_anim.setDuration(300)
		self._btn_00_fadein_anim.setStartValue(0.0)
		self._btn_00_fadein_anim.setEndValue(1.0)
		self._btn_00_fadein_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
		self._btn_00_fadein_anim.finished.connect(self._on_btn_00_fadein_finished)
		self._btn_00_fadein_anim.start()

	def _on_btn_00_fadein_finished(self):
		"""btn_00 淡入完成后清理"""
		self.btn_00.setGraphicsEffect(None)

	def pin_a_tab(self):
		# 使用 _current_screen_geometry 获取当前鼠标所在屏幕的尺寸
		screen_geom = self._current_screen_geometry()
		SCREEN_WEIGHT = int(screen_geom.width())
		SCREEN_HEIGHT = int(screen_geom.height())
		screen_x = screen_geom.x()  # 屏幕左上角的x坐标（多显示器时重要）
		screen_y = screen_geom.y()  # 屏幕左上角的y坐标
		x_center = 0
		y_center = 0
		if self.i % 2 == 1:  # show
			btna4.setChecked(True)
			# 先设置窗口透明度为0，防止闪现
			self.setWindowOpacity(0)
			# 设置 btn_00 的样式（动画会处理位置和尺寸）
			accent = get_accent_color_hex()
			self.btn_00.setStyleSheet(f'''
						border: 1px outset grey;
						background-color: {accent};
						border-radius: 4px;
						padding: 1px;
						color: #FFFFFF''')
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(1520, SCREEN_HEIGHT)
			# 调整内部组件以适应新的屏幕高度
			self._adjust_components_for_screen(SCREEN_HEIGHT)
			x_center = screen_x + int(SCREEN_WEIGHT / 2) - 760
			y_center = screen_y
			self.move(screen_x + int(SCREEN_WEIGHT / 2) - 760, screen_y - SCREEN_HEIGHT)
			# 显示窗口（透明状态）
			self.show()
			# 隐藏所有组件，动画会逐步显示它们
			self.qw0.setVisible(False)
			self.qw1.setVisible(False)
			self.l1.setVisible(False)
			self.btn_00.setVisible(False)
			self.btn0_1.setVisible(False)
			self.btn0_2.setVisible(False)
			self.btn0_sound.setVisible(False)
			self.btn0_tp.setVisible(False)
			self.btn0_web.setVisible(False)
			self.word_count_label.setVisible(False)
			self.updatecontent_for_mode()
			# 用 QTimer 延迟恢复透明度，确保隐藏操作已生效
			def restore_and_animate():
				self.setWindowOpacity(1)
				self._start_pin_show_animation(SCREEN_HEIGHT)
			QTimer.singleShot(50, restore_and_animate)
		if self.i % 2 == 0:  # hide
			if self.notes_mode_enabled and self.notes_dirty:
				self._notes_flush()   # 收起前把还没存的存进备忘录（自动保存，不再问）
			btna4.setChecked(False)

			# 定义隐藏动画完成后的回调
			def on_hide_complete():
				self.btn_00.setFixedHeight(10)
				self.btn_00.setFixedWidth(100)
				self.btn_00.setStyleSheet('''
							border: 1px outset grey;
							background-color: #FFFFFF;
							border-radius: 4px;
							padding: 1px;
							color: #000000''')
				self.btn_00.move(0, 0)
				self.btn0_2.setVisible(True)
				self.setFixedSize(100, 10)
				# 隐藏时移动到当前屏幕的顶部中央
				hide_x = screen_x + int(SCREEN_WEIGHT / 2) - 50
				hide_y = screen_y
				self.move(screen_x + int(SCREEN_WEIGHT / 2) - 50, screen_y + SCREEN_HEIGHT)
				self.move_window(hide_x, hide_y)
				self.btn_00.raise_()
				self.btn0_2.raise_()

			# 启动隐藏动画
			self._start_pin_hide_animation(SCREEN_HEIGHT, on_hide_complete)
			return  # 动画完成后会执行回调

		self.move_window(x_center, y_center)
		self.qw0.raise_()
		self.qw1.raise_()
		self.btn_00.raise_()
		self.btn0_1.raise_()
		self.word_count_label.raise_()
		self.btn0_2.raise_()
		self.btn0_sound.raise_()
		self.btn0_tp.raise_()
		self.btn0_web.raise_()

	def toggle_sound_mode(self):
		self.sound_mode_enabled = not self.sound_mode_enabled
		if self.sound_mode_enabled:
			self._show_mode_toast(_tr("Sound ON"))
		else:
			self._show_mode_toast(_tr("Sound OFF"))

	def _start_sound_monitor(self):
		"""使用 NSEvent local monitor 监听键盘，兼容所有输入法"""
		self._sound_monitor = None
		self._sound_key_handler = None
		try:
			from AppKit import NSEvent
		except ImportError:
			return

		NSEventMaskKeyDown = 1 << 10
		NSCommandKeyMask = 1 << 20
		NSControlKeyMask = 1 << 18
		w3_ref = self

		def key_handler(ns_event):
			try:
				if WEB_IME_DEBUG_LOG and w3_ref.web_mode_enabled and w3_ref.web_panel is not None and w3_ref.web_panel.has_typing_focus():
					flags0 = ns_event.modifierFlags()
					if not (flags0 & (NSCommandKeyMask | NSControlKeyMask)):
						_log_qt_ime_state('key press')
				if not w3_ref.sound_mode_enabled:
					return ns_event
				in_editor = w3_ref.bottom.hasFocus()
				in_web = (not in_editor) and w3_ref.web_mode_enabled and w3_ref.web_panel is not None and w3_ref.web_panel.has_typing_focus()
				if not in_editor and not in_web:
					return ns_event
				flags = ns_event.modifierFlags()
				if flags & (NSCommandKeyMask | NSControlKeyMask):
					return ns_event
				key_code = ns_event.keyCode()
				if key_code == 51 or key_code == 117:  # backspace / forward delete
					play_sound_async(BasePath + 'delete.wav')
					w3_ref._sound_bell_played = False
				elif key_code == 36 or key_code == 76:  # return / numpad enter
					play_sound_async(BasePath + 'return.wav')
					w3_ref._sound_bell_played = False
				else:
					chars = ns_event.charactersIgnoringModifiers()
					if chars and len(chars) > 0 and ord(chars[0]) >= 32 and ord(chars[0]) < 0xF700 and in_web:
						play_sound_async(BasePath + 'normal.wav')
					elif chars and len(chars) > 0 and ord(chars[0]) >= 32 and ord(chars[0]) < 0xF700:
						cursor_rect = w3_ref.bottom.cursorRect()
						viewport_width = w3_ref.bottom.viewport().width()
						char_width = w3_ref.bottom.fontMetrics().averageCharWidth()
						remaining = (viewport_width - cursor_rect.right()) / max(char_width, 1)
						if remaining <= 10:
							if not w3_ref._sound_bell_played:
								play_sound_async(BasePath + 'bell.mp3')
								w3_ref._sound_bell_played = True
							else:
								play_sound_async(BasePath + 'normal.wav')
						else:
							w3_ref._sound_bell_played = False
							play_sound_async(BasePath + 'normal.wav')
			except Exception:
				pass
			return ns_event

		self._sound_key_handler = key_handler
		self._sound_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
			NSEventMaskKeyDown, key_handler
		)

	def _stop_sound_monitor(self):
		if self._sound_monitor:
			try:
				from AppKit import NSEvent
				NSEvent.removeMonitor_(self._sound_monitor)
			except Exception:
				pass
			self._sound_monitor = None
			self._sound_key_handler = None

	def closeEvent(self, event):
		self._stop_mode_autobackup()
		self._stop_preview_rendering()
		self._stop_sound_monitor()
		self._stop_notes_wait()
		if self.notes_cache_worker:
			self.notes_cache_worker.stop()
			self.notes_cache_worker.wait(2000)
		if self._notes_focus_check_worker is not None and self._notes_focus_check_worker.isRunning():
			self._notes_focus_check_worker.wait(2000)
		if self.web_panel is not None:
			self.web_panel.save_now()
		self._flush_office_before_quit()
		self._notes_flush_before_quit()
		event.accept()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._update_hit_mask()
		if not DEBUG_LAYOUT:
			return
		try:
			old_size = event.oldSize()
			new_size = event.size()
			spontaneous = int(event.spontaneous())
			line = (
				f"{time.time():.3f} resize "
				f"old={old_size.width()}x{old_size.height()} "
				f"new={new_size.width()}x{new_size.height()} "
				f"spontaneous={spontaneous} "
				f"notes_mode={int(self.notes_mode_enabled)}\n"
			)
			with open(os.path.join(SettingsPath, "layout_debug.log"), "a", encoding="utf-8") as f0:
				f0.write(line)
			if self.qw0.isVisible() and new_size.width() not in (100, 1520):
				stack = "".join(traceback.format_stack(limit=12))
				with open(os.path.join(SettingsPath, "layout_debug.log"), "a", encoding="utf-8") as f0:
					f0.write(f"{time.time():.3f} resize_stack\n{stack}\n")
		except Exception:
			pass

	def updatecontent_for_mode(self):
		if self.notes_mode_enabled:
			self.reload_notes_on_show()
			if self.notes_loader and self.notes_loader.isRunning():
				return
			if self.notes_reload_pending:
				return
			current_index = self.widget_notes.currentIndex()
			if 0 <= current_index < len(self.notes_current_list):
				self.notes_index_change(current_index)
			else:
				self.bottom.blockSignals(True)
				self.bottom.clear()
				self.bottom.blockSignals(False)
				self.topleft.setHtml("", LOCAL_PAGE_BASE)
				self.topright.clear()
			return
		self._set_notes_active(False)
		self.updatecontent()

	def _start_mode_autobackup(self):
		if self.mode_backup_timer:
			self.mode_backup_timer.stop()
		self.mode_backup_timer = QTimer(self)
		self.mode_backup_timer.setInterval(60 * 1000)
		self.mode_backup_timer.timeout.connect(self._trigger_mode_autobackup)
		self.mode_backup_timer.start()

	def _stop_mode_autobackup(self):
		if self.mode_backup_timer:
			self.mode_backup_timer.stop()
			self.mode_backup_timer.deleteLater()
			self.mode_backup_timer = None

	def _trigger_mode_autobackup(self):
		if not self.notes_mode_enabled:
			self._trigger_local_mode_backup()

	def _current_local_file_path(self):
		home_dir = str(Path.home())
		app_dir = WATERMELON_DATA_DIR
		feed_file = os.path.join(app_dir, "DoNotDelete.txt")
		current_file = os.path.join(app_dir, "Current.txt")
		if not os.path.exists(feed_file) or not os.path.exists(current_file):
			return None
		try:
			paths = codecs.open(feed_file, 'r', encoding='utf-8').read()
			paths_list = [line for line in paths.split('\n') if line.strip()]
			if not paths_list:
				return None
			current_index = int(codecs.open(current_file, 'r', encoding='utf-8').read().strip() or "0")
			if current_index < 0 or current_index >= len(paths_list):
				return None
			parts = paths_list[current_index].split("||", 1)
			if len(parts) != 2:
				return None
			return parts[1]
		except Exception:
			return None

	def _backup_target_dir(self, backup_root, label, identity):
		safe_label = re.sub(r'[\\\\/:*?"<>|]', '_', (label or "").strip())
		if safe_label == "":
			safe_label = "Untitled"
		digest = hashlib.sha1(identity.encode('utf-8')).hexdigest()[:8]
		target_dir = os.path.join(backup_root, f"{safe_label}_{digest}")
		os.makedirs(target_dir, exist_ok=True)
		return target_dir

	def open_current_backup_folder(self):
		target_dir = ""
		if self.notes_mode_enabled:
			note_key = self._current_notes_key()
			title = self.notes_current_title or (self.widget_notes.currentText().strip() if hasattr(self, "widget_notes") else "") or "Untitled"
			if note_key:
				target_dir = self._backup_target_dir(self.notes_mode_backup_root, title, note_key)
			else:
				target_dir = self.notes_mode_backup_root
		else:
			source_path = self._current_local_file_path()
			if source_path:
				label = Path(source_path).stem
				target_dir = self._backup_target_dir(self.local_mode_backup_root, label, source_path)
			else:
				target_dir = self.local_mode_backup_root
		try:
			os.makedirs(target_dir, exist_ok=True)
			subprocess.call(['open', target_dir])
		except Exception:
			pass

	def _perform_mode_backup(self, target_dir, content, extension='.md'):
		with self._mode_backup_lock:
			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
			backup_path = os.path.join(target_dir, f"{timestamp}{extension}")
			try:
				if isinstance(content, bytes):
					with open(backup_path, 'wb') as fp:
						fp.write(content)
				else:
					with open(backup_path, 'w', encoding='utf-8') as fp:
						fp.write(content)
			except Exception:
				return
			self._enforce_mode_backup_limit(target_dir, load_mode_backup_limit())

	def _enforce_mode_backup_limit(self, target_dir, limit):
		if limit <= 0:
			return
		try:
			md_files = [
				os.path.join(target_dir, f)
				for f in os.listdir(target_dir)
				if f.endswith(('.md',) + tuple(watermelon_office.OFFICE_EDITOR_EXTS))
			]
		except Exception:
			return
		if len(md_files) <= limit:
			return
		md_files.sort(key=os.path.getmtime)
		for old_file in md_files[:-limit]:
			try:
				os.remove(old_file)
			except Exception:
				continue

	def apply_backup_limit_now(self, limit=None):
		if limit is None:
			limit = load_mode_backup_limit()
		roots = [self.local_mode_backup_root, self.notes_mode_backup_root]
		for root in roots:
			if not root or not os.path.isdir(root):
				continue
			try:
				names = os.listdir(root)
			except Exception:
				continue
			for name in names:
				sub_dir = os.path.join(root, name)
				if os.path.isdir(sub_dir):
					self._enforce_mode_backup_limit(sub_dir, limit)

	def _trigger_local_mode_backup(self):
		source_path = self._current_local_file_path()
		if not source_path or not os.path.exists(source_path):
			return
		try:
			current_meta = (os.path.getmtime(source_path), os.path.getsize(source_path))
		except Exception:
			return
		prev_meta = self._last_local_backup_meta.get(source_path)
		if prev_meta is None:
			self._last_local_backup_meta[source_path] = current_meta
			return
		if prev_meta == current_meta:
			return
		self._last_local_backup_meta[source_path] = current_meta
		try:
			if is_office_path(source_path):
				with open(source_path, 'rb') as fp:
					content = fp.read()   # Office 文件：备份整个文件
			else:
				with open(source_path, 'r', encoding='utf-8') as fp:
					content = fp.read()
		except Exception:
			return
		label = Path(source_path).stem
		target_dir = self._backup_target_dir(self.local_mode_backup_root, label, source_path)
		threading.Thread(
			target=self._perform_mode_backup,
			args=(target_dir, content, os.path.splitext(source_path)[1].lower() if is_office_path(source_path) else '.md'),
			daemon=True
		).start()

	def _backup_notes_mode_if_changed(self, note_key, title, note_md):
		if not note_key:
			return
		current_hash = hashlib.sha1(note_md.encode('utf-8')).hexdigest()
		prev_hash = self._last_notes_backup_hash.get(note_key)
		if prev_hash == current_hash:
			return
		self._last_notes_backup_hash[note_key] = current_hash
		title = title or "Untitled"
		target_dir = self._backup_target_dir(self.notes_mode_backup_root, title, note_key)
		threading.Thread(
			target=self._perform_mode_backup,
			args=(target_dir, note_md),
			daemon=True
		).start()

	def _show_custom_message_box(self, title, text, buttons, default=0):
		"""提醒 / 询问 = 系统提醒（样式书 5.7：圆角 26，出现在主窗口上方；回车 = 默认按钮，Esc = Cancel）。
		返回选中按钮的序号；Esc / 关掉 = Cancel 的序号，没有 Cancel 时是 -1。"""
		buttons = [str(b) for b in buttons]
		default_label = buttons[max(0, min(int(default or 0), len(buttons) - 1))]
		escape = _tr('Cancel') if _tr('Cancel') in buttons else None
		chosen = watermelon_choice(self, title, text, buttons, default_label, escape=escape)
		return buttons.index(chosen) if chosen in buttons else -1

	def _refresh_notes_from_source(self):
		if self.notes_loader and self.notes_loader.isRunning():
			return
		self.notes_refresh_in_progress = True
		self.notes_loader = NotesLoader(self)
		self.notes_loader.finished.connect(self._on_notes_loader_finished)
		self.notes_loader.error.connect(self._on_notes_loader_error)
		self.notes_loader.start()

	def _on_notes_loader_finished(self, notes):
		if self.notes_loader:
			self.notes_loader.deleteLater()
			self.notes_loader = None
		self.notes_refresh_in_progress = False
		try:
			_write_notes_cache(notes, self.notes_cache_path)
		except Exception:
			pass
		self.on_notes_loaded(notes)

	def _on_notes_loader_error(self, message):
		if self.notes_loader:
			self.notes_loader.deleteLater()
			self.notes_loader = None
		self.notes_refresh_in_progress = False
		self.on_notes_error(message)

	def _prompt_notes_reselect(self, folder, title):
		# 如果已经在等待用户重新选择，不要重复弹窗
		if self.notes_awaiting_reselect:
			return
		# 确保 bottom 被锁定
		self._set_notes_active(False)
		location = folder or "Unfiled"
		result = self._show_custom_message_box(
			title=_tr("Note Not Found"),
			text=_tr('Couldn\'t match the current note "%1" in "%2".\nPlease reselect the note path.').replace(
				'%1', str(title)).replace('%2', str(location)),
			buttons=(_tr("OK"), _tr("Cancel")),
			default=0,
		)
		if result == 0:
			self.notes_awaiting_reselect = True
			self.open_notes_folder_dialog()
		# 无论选择 OK 还是 Cancel，bottom 都保持锁定状态直到选择有效路径

	def _notes_title_from_md(self, md):
		if not md:
			return ""
		for line in md.splitlines():
			stripped = line.strip()
			if not stripped:
				continue
			try:
				html = markdown_to_html(stripped)
			except Exception:
				return stripped
			plain = normalize_ws(strip_tags(html))
			return plain or stripped
		return ""

	def updatecontent(self):
		# set text
		current_index = self.widget0.currentIndex()
		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)

		with open(fulldir4, 'w', encoding='utf-8') as f0:
			f0.write(str(current_index))

		paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = paths.split('\n')
		while '' in pathslist:
			pathslist.remove('')
		current_path = pathslist[current_index].split('||')[1]
		try:
			previewtext = _read_local_text(current_path)
			self.widget0.setCurrentIndex(current_index)
		except Exception as e:
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			currentindex = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
			self.widget0.setCurrentIndex(currentindex)
		pos = int(codecs.open(SettingsPath + 'text_position.txt', 'r', encoding='utf-8').read())
		self.bottom.setText(previewtext)
		self.bottom.ensureCursorVisible()  # 游标可用
		cursor = self.bottom.textCursor()  # 设置游标
		cursor.setPosition(min(pos, len(previewtext)))  # 游标位置设置为尾部
		self.bottom.setTextCursor(cursor)  # 滚动到游标位置
		self._request_async_preview_render(previewtext, debounce_ms=0)
		self._sync_office_view()

	def _request_async_preview_render(self, markdown_text, debounce_ms=90):
		self._update_word_count_label()
		self._refresh_attachment_rail(markdown_text)
		self._preview_render_request_token += 1
		self._preview_render_pending_text = markdown_text
		self._preview_render_pending_token = self._preview_render_request_token
		if debounce_ms <= 0:
			self._preview_render_timer.stop()
			self._start_preview_render_worker()
			return
		self._preview_render_timer.start(debounce_ms)

	def _start_preview_render_worker(self):
		if self._preview_render_worker and self._preview_render_worker.isRunning():
			return
		if self._preview_render_pending_text is None:
			return
		markdown_text = self._preview_render_pending_text
		request_id = self._preview_render_pending_token
		self._preview_render_pending_text = None
		render_left = self.topleftshow == 1
		render_right = self.toprightshow == 1
		if not render_left and not render_right:
			return
		worker = PreviewRenderWorker(
			request_id=request_id,
			markdown_text=markdown_text,
			render_left=render_left,
			render_right=render_right,
			parent=self,
		)
		worker.rendered.connect(self._on_preview_rendered)
		worker.failed.connect(self._on_preview_render_failed)
		worker.finished.connect(self._on_preview_worker_finished)
		worker.finished.connect(worker.deleteLater)
		self._preview_render_worker = worker
		worker.start()

	def _on_preview_rendered(self, request_id, left_markdown_html, right_markdown_html):
		if request_id != self._preview_render_request_token:
			return
		if self.topleftshow == 1 and left_markdown_html is not None:
			self.topleft.setHtml(self.md2html("", pre_rendered_html=left_markdown_html), LOCAL_PAGE_BASE)
		if self.toprightshow == 1 and right_markdown_html is not None:
			self.topright.setHtml(self.md2html("", pre_rendered_html=right_markdown_html))

	def _on_preview_render_failed(self, request_id, _error_message):
		if request_id != self._preview_render_request_token:
			return
		# Keep UI responsive even when a render task fails.
		return

	def _on_preview_worker_finished(self):
		self._preview_render_worker = None
		if self._preview_render_pending_text is not None:
			QTimer.singleShot(0, self._start_preview_render_worker)

	def _stop_preview_rendering(self):
		self._preview_render_timer.stop()
		self._preview_render_pending_text = None
		worker = self._preview_render_worker
		if worker and worker.isRunning():
			worker.requestInterruption()
			worker.wait(500)
		self._preview_render_worker = None

	def _read_font_size(self, default=14):
		try:
			return int(codecs.open(SettingsPath + 'fs.txt', 'r', encoding='utf-8').read())
		except Exception:
			return default

	def _resolve_font_family(self, fallback=None):
		try:
			font_family = codecs.open(SettingsPath + 'lastused.txt', 'r', encoding='utf-8').read().strip()
		except Exception:
			return fallback or default_font_family()
		if font_family in ('0', ''):
			return default_font_family()
		return font_family

	def set_textedit_font(self, size, family):
		self._current_font_size = size
		self._current_font_family = family
		font_override = f"""
QTextEdit{{
	font: {size}pt {family};
}}
QListWidget{{
	font: {size}pt {family};
}}
"""
		app = QApplication.instance()
		if app is not None:
			base_style = style_sheet_dark if is_dark_theme(app) else style_sheet_ori
			app.setStyleSheet(base_style + "\n" + font_override)
			if hasattr(self, "bottom") and hasattr(self, "topleft") and hasattr(self, "topright"):
				try:
					previewtext = self.bottom.toPlainText()
					self._request_async_preview_render(previewtext, debounce_ms=0)
				except Exception:
					pass
		# 重新应用用户选择的背景颜色
		if hasattr(self, "_current_bg_color") and hasattr(self, "topleft"):
			self.set_bg_color(self._current_bg_color)

	def splitter1_move(self):
		if self.topleft.width() == 0 or self.topleft.height() == 0:
			self.topleftshow = 0
		if self.topleft.width() != 0 and self.topleft.height() != 0:
			self.topleftshow = 1
		if self.topright.width() == 0 or self.topright.height() == 0:
			self.toprightshow = 0
		if self.topright.width() != 0 and self.topright.height() != 0:
			self.toprightshow = 1

	def splitter2_move(self):
		if self.topleft.width() == 0 or self.topleft.height() == 0:
			self.topleftshow = 0
		if self.topleft.width() != 0 and self.topleft.height() != 0:
			self.topleftshow = 1
		if self.topright.width() == 0 or self.topright.height() == 0:
			self.toprightshow = 0
		if self.topright.width() != 0 and self.topright.height() != 0:
			self.toprightshow = 1
		sizes = self.splitter2.sizes()
		total = sum(sizes)
		if total > 0:
			self._splitter2_ratio = sizes[0] / total
			self._splitter2_user_set = True

	def text_change(self):
		if getattr(self, 'lecture_session', None) is not None and self.lecture_mode_enabled:
			self.lecture_session.note_changed()     # 听课时新写的一段：停笔一会儿就发过去做卡片
		if self.notes_active:
			self._set_notes_dirty(True)
			previewtext = self.bottom.toPlainText()
			self._request_async_preview_render(previewtext, debounce_ms=90)
			QTimer.singleShot(100, self.scrollchanged)
			return
		# 如果处于 Notes 模式但 notes_active 为 False，不要保存到普通模式文件
		if self.notes_mode_enabled:
			# 只更新预览，不保存文件
			previewtext = self.bottom.toPlainText()
			self._request_async_preview_render(previewtext, debounce_ms=90)
			QTimer.singleShot(100, self.scrollchanged)
			return
		if is_office_path(self._current_local_file_path() or ''):
			return   # 当前是 Office 文件：由 Office 面板自己保存，文字框里的东西绝不写进它
		if self.bottom.toPlainText() != '':
			# set text
			home_dir = str(Path.home())
			fulldir1 = WATERMELON_DATA_DIR
			if not os.path.exists(fulldir1):
				os.mkdir(fulldir1)
			tarname2 = "DoNotDelete.txt"
			fulldir2 = os.path.join(fulldir1, tarname2)
			if not os.path.exists(fulldir2):
				with open(fulldir2, 'a', encoding='utf-8') as f0:
					f0.write('')
			tarname3 = "Note 001.md"
			fulldir3 = os.path.join(fulldir1, tarname3)
			tarname4 = "Current.txt"
			fulldir4 = os.path.join(fulldir1, tarname4)
			if not os.path.exists(fulldir4):
				with open(fulldir4, 'a', encoding='utf-8') as f0:
					f0.write('0')

			paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
			targetpath = fulldir3
			if paths == '':
				with open(fulldir3, 'a', encoding='utf-8') as f0:
					f0.write(self.bottom.toPlainText())
				with open(fulldir2, 'w', encoding='utf-8') as f0:
					f0.write('Note 001||' + fulldir3 + '\n')
				self.widget0.clear()
				paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
				pathslist = paths.split('\n')
				while '' in pathslist:
					pathslist.remove('')
				namelist = []
				for i in range(len(pathslist)):
					namelist.append(pathslist[i].split('||')[0])
				self.widget0.addItems(namelist)
				self.widget0.setCurrentIndex(0)
				with open(fulldir4, 'a', encoding='utf-8') as f0:
					f0.write('0')
				targetpath = fulldir3
			if paths != '':
				pathslist = paths.split('\n')
				while '' in pathslist:
					pathslist.remove('')
				currentfile = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
				targetpath = pathslist[currentfile].split('||')[1]
				with open(targetpath, 'w', encoding='utf-8') as f0:
					f0.write(self.bottom.toPlainText())
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			self._request_async_preview_render(previewtext, debounce_ms=90)
			# set position
			QTimer.singleShot(100, self.scrollchanged)

	def scrollchanged(self):
		if self.bottom.verticalScrollBar().maximum() != 0:
			proportion = self.bottom.verticalScrollBar().value() / self.bottom.verticalScrollBar().maximum()
			if self.topleftshow == 1:
				if hasattr(self.topleft, "verticalScrollBar"):
					tar_pro = int(self.topleft.verticalScrollBar().maximum() * proportion)
					self.topleft.verticalScrollBar().setValue(tar_pro)
				else:
					self._set_webview_scroll_by_proportion(self.topleft, proportion)
			if self.toprightshow == 1:
				tar_pro2 = int(self.topright.verticalScrollBar().maximum() * proportion)
				self.topright.verticalScrollBar().setValue(tar_pro2)

	def _set_webview_scroll_by_proportion(self, view, proportion):
		# QWebEngineView does not expose scroll bars; use JS to scroll instead.
		if proportion < 0:
			proportion = 0
		elif proportion > 1:
			proportion = 1
		js = """
		(function(){
			const doc = document.documentElement;
			const body = document.body;
			const scrollHeight = Math.max(doc.scrollHeight, body.scrollHeight);
			const clientHeight = doc.clientHeight;
			const maxScroll = Math.max(0, scrollHeight - clientHeight);
			const target = Math.floor(maxScroll * %s);
			window.scrollTo(0, target);
		})();
		""" % ("{:.6f}".format(proportion))
		try:
			view.page().runJavaScript(js)
		except Exception:
			pass

	def cursorchanged(self):
		self.bottom.ensureCursorVisible()  # 游标可用
		cursor = self.bottom.textCursor()  # 设置游标
		position = cursor.position()
		self._update_word_count_label()
		if self.notes_mode_enabled and self.notes_active:
			note_key = self._current_notes_key()
			if note_key:
				scrollbar = self.bottom.verticalScrollBar()
				scroll_proportion = 0
				if scrollbar.maximum() != 0:
					scroll_proportion = scrollbar.value() / scrollbar.maximum()
				self._notes_positions[note_key] = {
					"cursor": position,
					"scroll_proportion": scroll_proportion,
				}
			return
		fullcontent = self.bottom.toPlainText()
		list_fullcontent = list(fullcontent)
		remove_list = list_fullcontent[:position]
		proportion = len(remove_list)
		with open(SettingsPath + 'text_position.txt', 'w', encoding='utf-8') as f0:
				f0.write(str(proportion))

	def _current_notes_key(self):
		if not self.notes_current_title:
			return None
		folder = (self.notes_current_folder or "Unfiled").strip() or "Unfiled"
		title = self.notes_current_title or "(Untitled)"
		return f"{folder}/{title}"

	def _restore_notes_position(self, note_key):
		if not note_key:
			return
		data = self._notes_positions.get(note_key)
		if not data:
			return
		pos = data.get("cursor", 0)
		if pos < 0:
			pos = 0
		text_len = len(self.bottom.toPlainText())
		if pos > text_len:
			pos = text_len
		try:
			cursor = self.bottom.textCursor()
			cursor.setPosition(pos)
			self.bottom.setTextCursor(cursor)
			self.bottom.ensureCursorVisible()
			scroll_proportion = data.get("scroll_proportion")
			if scroll_proportion is not None:
				scrollbar = self.bottom.verticalScrollBar()
				if scrollbar.maximum() != 0:
					scrollbar.setValue(int(scrollbar.maximum() * scroll_proportion))
			QTimer.singleShot(50, self.scrollchanged)
		except Exception:
			pass

	def open_file(self):
		home_dir = str(Path.home())
		office_ready = watermelon_office.load_component(BasePath)[0] is not None
		file_filter = _tr("Documents (*.md *.docx *.xlsx *.pptx)") if office_ready else _tr("Markdown Files (*.md)")
		fj = QFileDialog.getOpenFileName(self, _tr("Open File"), home_dir, file_filter)
		if fj[0] != '':
			self.open_local_path(fj[0])

	def open_local_path(self, str_fj):
		"""Open 选好文件以后做的事（工具也走这里）：加进文件下拉并切到它。"""
		if True:
			if is_office_path(str_fj):
				self._open_office_file(str_fj)
				return
			text_open = codecs.open(str_fj, 'r', encoding='utf-8').read()
			# set list
			fulldir1 = WATERMELON_DATA_DIR
			tarname2 = "DoNotDelete.txt"
			fulldir2 = os.path.join(fulldir1, tarname2)
			open_title = str_fj.split('/')[-1].replace('.md', '')
			with open(fulldir2, 'a', encoding='utf-8') as f0:
				f0.write(open_title + '||' + str_fj + '\n')
			namelist = []
			namelist.append(open_title)
			self.widget0.addItems(namelist)
			self.widget0.setCurrentIndex(self.widget0.count() - 1)
			# set index
			tarname4 = "Current.txt"
			fulldir4 = os.path.join(fulldir1, tarname4)
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write(str(self.widget0.currentIndex()))
			# set text
			self.bottom.setText(text_open)
			self.bottom.ensureCursorVisible()  # 游标可用
			cursor = self.bottom.textCursor()  # 设置游标
			pos = len(self.bottom.toPlainText())  # 获取文本尾部的位置
			cursor.setPosition(pos)  # 游标位置设置为尾部
			self.bottom.setTextCursor(cursor)  # 滚动到游标位置
			self._request_async_preview_render(text_open, debounce_ms=0)

	def new_file(self):
		self.bottom.clear()
		self.topleft.setHtml("", LOCAL_PAGE_BASE)
		self.topright.clear()

		current_time = datetime.now().strftime('%Y-%m-%d %f')
		newfile_name = 'Note ' + current_time
		newfile_name_full = 'Note ' + current_time + ".md"
		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		fulldir_new = os.path.join(fulldir1, newfile_name_full)
		with open(fulldir_new, 'a', encoding='utf-8') as f0:
			f0.write('')

		# set list
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		with open(fulldir2, 'a', encoding='utf-8') as f0:
			f0.write(newfile_name + '||' + fulldir_new + '\n')
		namelist = []
		namelist.append(newfile_name)
		self.widget0.addItems(namelist)
		self.widget0.setCurrentIndex(self.widget0.count() - 1)

		# set index
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)
		with open(fulldir4, 'w', encoding='utf-8') as f0:
			f0.write(str(self.widget0.currentIndex()))

	def index_change(self, i):
		self._set_notes_active(False)
		self.bottom.clear()
		self.topleft.setHtml("", LOCAL_PAGE_BASE)
		self.topright.clear()

		# set text
		current_index = i
		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)

		with open(fulldir4, 'w', encoding='utf-8') as f0:
			f0.write(str(i))

		paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = paths.split('\n')
		while '' in pathslist:
			pathslist.remove('')
		current_path = pathslist[current_index].split('||')[1]
		try:
			previewtext = _read_local_text(current_path)
			self.widget0.setCurrentIndex(current_index)
		except Exception as e:
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			currentindex = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
			self.widget0.setCurrentIndex(currentindex)
		self.bottom.setText(previewtext)
		self._request_async_preview_render(previewtext, debounce_ms=0)
		self._sync_office_view()

	def _set_notes_dirty(self, dirty):
		"""有没有还没存进备忘录的修改。有 → 停笔 NOTES_AUTOSAVE_DELAY_MS 后自动存（2026-11-21 Ryan：
		“save 就是一个自动 save 的功能”）。状态显示在字数那一行的末尾。"""
		self.notes_dirty = bool(dirty)
		if self.notes_dirty:
			if self._notes_save_state in ('saved', ''):
				self._notes_save_state = ''
			self._notes_save_timer.start(NOTES_AUTOSAVE_DELAY_MS)
		else:
			self._notes_save_timer.stop()
		self._update_word_count_label()

	def _set_notes_active(self, active):
		self.notes_active = bool(active)
		self.btn_notes_open.setEnabled(self.notes_active)
		# 在 Notes 模式下，根据 active 状态控制 bottom 是否可编辑
		if self.notes_mode_enabled:
			self.bottom.setReadOnly(not self.notes_active)
		if not self.notes_active:
			self._set_notes_dirty(False)
		self._update_word_count_label()

	def _set_notes_new_enabled(self, enabled):
		self.btn_notes_new.setEnabled(bool(enabled))

	def _set_notes_export_enabled(self, enabled):
		self.btn_notes_export.setEnabled(bool(enabled))

	# def _enforce_window_width(self):
	# 	if not self.qw0.isVisible():
	# 		return
	# 	if self.width() == 1520:
	# 		return
	# 	screen_geom = self._current_window_screen_geometry()
	# 	self._apply_screen_geometry(screen_geom)

	def _show_mode_toast(self, mode_name):
		"""显示模式切换提示，自动消失"""
		toast = QLabel(mode_name, self)
		toast.setStyleSheet('''
			QLabel {
				background-color: rgba(0, 0, 0, 0.7);
				color: white;
				padding: 15px 30px;
				border-radius: 10px;
				font-size: 18px;
				font-weight: bold;
			}
		''')
		toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
		toast.adjustSize()
		# 居中显示
		toast.move(
			(self.width() - toast.width()) // 2,
			(self.height() - toast.height()) // 2
		)
		toast.show()
		toast.raise_()
		# 1.5秒后自动消失
		QTimer.singleShot(1500, toast.deleteLater)

	def _log_layout_state(self, tag):
		if not DEBUG_LAYOUT:
			return
		try:
			qw0_geo = self.qw0.geometry()
			qw1_geo = self.qw1.geometry()
			splitter2_geo = self.splitter2.geometry()
			splitter1_geo = self.splitter1.geometry()
			l1_geo = self.l1.geometry()
			main_geo = self.geometry()
			main_hint = self.sizeHint()
			qw0_hint = self.qw0.sizeHint()
			qw1_hint = self.qw1.sizeHint()
			splitter2_hint = self.splitter2.sizeHint()
			splitter1_hint = self.splitter1.sizeHint()
			main_min = self.minimumSize()
			main_max = self.maximumSize()
			layout_hint = self.layout().sizeHint() if self.layout() else QSize(0, 0)
			layout_min = self.layout().minimumSize() if self.layout() else QSize(0, 0)
			try:
				left_doc_w = float(self.topleft.document().size().width())
				right_doc_w = float(self.topright.document().size().width())
			except Exception:
				left_doc_w = -1.0
				right_doc_w = -1.0
			line = (
				f"{time.time():.3f} {tag} "
				f"main={main_geo.getRect()} "
				f"main_hint={main_hint.width()}x{main_hint.height()} "
				f"main_min={main_min.width()}x{main_min.height()} "
				f"main_max={main_max.width()}x{main_max.height()} "
				f"layout_hint={layout_hint.width()}x{layout_hint.height()} "
				f"layout_min={layout_min.width()}x{layout_min.height()} "
				f"qw0={qw0_geo.getRect()} qw1={qw1_geo.getRect()} "
				f"qw0_hint={qw0_hint.width()}x{qw0_hint.height()} "
				f"qw1_hint={qw1_hint.width()}x{qw1_hint.height()} "
				f"splitter2={splitter2_geo.getRect()} splitter1={splitter1_geo.getRect()} "
				f"splitter2_hint={splitter2_hint.width()}x{splitter2_hint.height()} "
				f"splitter1_hint={splitter1_hint.width()}x{splitter1_hint.height()} "
				f"l1={l1_geo.getRect()} "
				f"doc_w={left_doc_w:.1f}/{right_doc_w:.1f} "
				f"notes_mode={int(self.notes_mode_enabled)} "
				f"local_visible={int(self.btn_sub1.isVisible())} "
				f"notes_visible={int(self.btn_notes_folder.isVisible())}\n"
			)
			with open(os.path.join(SettingsPath, "layout_debug.log"), "a", encoding="utf-8") as f0:
				f0.write(line)
		except Exception:
			pass

	def _apply_mode_visibility(self):
		self.qw1.setUpdatesEnabled(False)
		local_widgets = (self.btn_sub1, self.btn_sub2, self.widget0, self.btn_sub3, self.btn_sub4)
		notes_widgets = (self.btn_notes_folder, self.widget_notes, self.btn_notes_open, self.btn_notes_new, self.btn_notes_export)
		if self.web_mode_enabled:
			shown = self._web_row_widgets
		elif self.notes_mode_enabled:
			shown = notes_widgets
		else:
			shown = local_widgets
		for widget in local_widgets + notes_widgets + self._web_row_widgets:
			if widget not in shown:
				widget.setVisible(False)
		for widget in shown:
			widget.setVisible(True)
		self.qw1.setUpdatesEnabled(True)
		self.qw1.updateGeometry()
		self._update_word_count_label()

	def _apply_notes_folder(self, folder, note_title=None):
		self.notes_current_folder = folder
		self._set_notes_new_enabled(bool(folder))
		self._set_notes_export_enabled(bool(folder))
		self.notes_current_list = []
		for note in self.notes_data:
			note_folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
			if note_folder == folder:
				self.notes_current_list.append(note)
		self.widget_notes.blockSignals(True)
		self.widget_notes.clear()
		for note in self.notes_current_list:
			title = note.get("title") or "(Untitled)"
			self.widget_notes.addItem(title, note)
		self.widget_notes.blockSignals(False)
		if self.notes_current_list:
			self.widget_notes.setEnabled(True)
			target_index = 0
			if note_title:
				for idx, note in enumerate(self.notes_current_list):
					title = note.get("title") or "(Untitled)"
					if title == note_title:
						target_index = idx
						break
			# 只改选中项、不发 currentIndexChanged：调用方 _select_note_by_folder_title 随后会
			# 显式调用一次 notes_index_change。以前目标不是第 0 项时，正文会被连续读两遍（两次 osascript）。
			self.widget_notes.blockSignals(True)
			self.widget_notes.setCurrentIndex(target_index)
			self.widget_notes.blockSignals(False)
		else:
			self.widget_notes.setEnabled(False)
			self._set_notes_active(False)
			self.notes_force_reload = False
			self.bottom.blockSignals(True)
			self.bottom.clear()
			self.bottom.blockSignals(False)
			self.topleft.setHtml("", LOCAL_PAGE_BASE)
			self.topright.clear()

	def _note_in_cache(self, notes, folder, title):
		for note in notes:
			note_folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
			note_title = note.get("title") or "(Untitled)"
			if note_title == title and note_folder == folder:
				return True
		return False

	def _start_notes_wait(self, folder, title):
		self.notes_wait_target = (folder, title)
		self.notes_wait_start = time.time()
		if not self.notes_wait_dialog:
			# 「请稍等」小卡片：窗口玻璃、圆角 16、不拦操作（样式书 5.12「同步中小卡片」）
			self.notes_wait_dialog = BusyCard(_tr("Updating Notes, please wait..."), size=(260, 90))
			self.notes_wait_dialog.setWindowTitle(_tr("Updating Notes"))
			self.notes_wait_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
			self.notes_wait_dialog.destroyed.connect(self._notes_wait_dialog_destroyed)
			# 居中显示
			screen = QGuiApplication.primaryScreen()
			if screen:
				geo = screen.availableGeometry()
				x = geo.x() + (geo.width() - 260) // 2
				y = geo.y() + (geo.height() - 90) // 2
				self.notes_wait_dialog.move(x, y)
		self.notes_wait_dialog.show()
		# 马上重扫一次，新笔记/新标题尽快出现在缓存里，不用干等下一轮
		self._request_notes_cache_refresh()
		if not self.notes_wait_timer:
			self.notes_wait_timer = QTimer(self)
			self.notes_wait_timer.setInterval(1000)
			self.notes_wait_timer.timeout.connect(self._check_notes_cache_for_wait)
		self.notes_wait_timer.start()

	def _stop_notes_wait(self):
		if self.notes_wait_timer:
			self.notes_wait_timer.stop()
		if self.notes_wait_dialog:
			self.notes_wait_dialog.close()
			self.notes_wait_dialog = None
		self.notes_wait_target = None
		self.notes_wait_start = None

	def _notes_wait_dialog_destroyed(self, _obj=None):
		if self.notes_wait_timer:
			self.notes_wait_timer.stop()
		self.notes_wait_dialog = None
		self.notes_wait_target = None
		self.notes_wait_start = None

	def _check_notes_cache_for_wait(self):
		if not self.notes_wait_target:
			self._stop_notes_wait()
			return
		if self.notes_wait_start and (time.time() - self.notes_wait_start) > 30:
			self._stop_notes_wait()
			return
		folder, title = self.notes_wait_target
		notes, error = _read_notes_cache(self.notes_cache_path)
		if error:
			return
		if self._note_in_cache(notes, folder, title):
			self._stop_notes_wait()
			self.notes_pending_title = title
			self.notes_pending_folder = folder
			self.notes_reload_pending = True
			self.notes_force_reload = True
			self.on_notes_loaded(notes)

	def _read_note_html(self, folder, title, note_id=None):
		return _read_note_html_from_notes(folder, title, note_id)

	def reload_notes_on_show(self):
		if not self.notes_mode_enabled:
			return
		if not self.notes_current_folder and not self.notes_folder_dialog:
			return
		self.notes_last_folder = self.notes_current_folder
		self.notes_last_title = self.notes_current_title
		self.notes_require_match_on_show = True
		self.notes_reload_pending = True
		self.notes_force_reload = True
		self._refresh_notes_from_source()

	def toggle_notes_mode(self):
		self._log_layout_state("toggle_before")
		if self.notes_mode_enabled and self.notes_dirty:
			self._notes_flush()   # 离开备忘录模式前把没存的存进去
		self.notes_mode_enabled = not self.notes_mode_enabled
		if self.notes_mode_enabled:
			# self.btn_mode.setText('Mode: Notes')
			self.btn0_2.setIconPath(BasePath + 'repeat2.png')
		else:
			# self.btn_mode.setText('Mode: Local')
			self.btn0_2.setIconPath(BasePath + 'repeat.png')
			self._set_notes_active(False)
			# 切换回普通模式时，恢复 bottom 为可编辑状态
			self.bottom.setReadOnly(False)
		self._apply_mode_visibility()
		self.updatecontent_for_mode()
		self._sync_office_view()
		if self.notes_mode_enabled:
			# 后台扫描线程可能正睡在 Local 模式的长间隔里，叫醒它改用 Notes 模式的短间隔。
			# 放在 updatecontent_for_mode 之后：若切换时已经开始重新扫描，它看到后只会改间隔，不会再并行扫一次。
			self._request_notes_cache_refresh()
		self._update_word_count_label()
		QTimer.singleShot(50, lambda: self._log_layout_state("toggle_after"))
		# 显示模式切换提示
		mode_name = _tr("Notes Mode") if self.notes_mode_enabled else _tr("Local Mode")
		self._show_mode_toast(mode_name)

	# ---------- Office 文件（Word / Excel / PowerPoint）----------
	# 2026-11-20 Ryan：“用那个下拉栏去切换”“把它包起来…不要让它孤零零的就这么露出来”。
	# Office 文件和 Markdown 在同一个文件下拉里；选中 Office 文件时，上面两栏预览和文字框一起让位，整列换成
	# 带细边框的 Office 编辑组件（和网页模式那一块同一个位置、同一种边框）；选回 Markdown 就换回来。
	# 组件停笔后自动存回原文件；切到别的文件 / 模式、收起、退出前再存一次。
	def _office_shown(self):
		return self.office_panel is not None and not self.office_panel.isHidden() and not self.web_mode_enabled

	def _ensure_office_panel(self):
		if self.office_panel is not None:
			return True
		component, reason = watermelon_office.load_component(BasePath)
		if component is None:
			logging.warning('Office files cannot be shown: %s', reason)
			return False
		panel = OfficePanel(component, language=UI_LANGUAGE, dark_getter=lambda: is_dark_theme(app), parent=self.qw0)
		panel.setFixedWidth(self.bottom.minimumWidth() or 1235)
		panel.hide()
		layout = self.qw0.layout()
		layout.insertWidget(layout.indexOf(self.splitter2) + 1, panel)
		panel.installEventFilter(self)   # 点击穿透的形状跟着 Office 区走
		panel.saveFailed.connect(self._on_office_save_failed)
		panel.switchRefused.connect(self._on_office_switch_refused)
		watermelon_ui._THEME_HOOKS.append(lambda _dark, p=panel: p.apply_theme())
		self.office_panel = panel
		return True

	def _sync_office_view(self):
		"""编辑区这一列该显示哪一块：网页 / Office 文件 / 两栏预览加文字框。每次换文件、换模式之后调用。"""
		path = None if self.notes_mode_enabled else self._current_local_file_path()
		office = bool(path and is_office_path(path)) and self._ensure_office_panel()
		show_office = office and not self.web_mode_enabled
		if office:
			self.office_panel.show_file(path)
		if self.office_panel is not None and not show_office:
			self.office_panel.leave()
		# 这一列一次只放一块：先把不该显示的藏起来，再显示该显示的。两块同时显示哪怕一瞬间，窗口都会被撑宽，
		# 而且不会缩回去（2026-11-20 Ryan：“这个位置是怎么回事，和其他的正常的窗口位置不一样”）。
		blocks = ((self.web_panel, self.web_mode_enabled), (self.office_panel, show_office),
				  (self.splitter2, not self.web_mode_enabled and not show_office))
		for block, wanted in blocks:
			if block is not None and not wanted:
				block.hide()
		for block, wanted in blocks:
			if block is not None and wanted:
				block.show()
		# Office 文件时：Clear 变灰（清空一份 Word 文件太危险）；提词器、打字声音用不上
		self.btn_sub4.setEnabled(not office)
		self.btn0_tp.setEnabled(not self.web_mode_enabled and not show_office)
		self.btn0_sound.setEnabled(not show_office)
		self._refresh_marks()
		self._update_word_count_label()
		self._update_hit_mask()

	def _local_file_list(self):
		"""文件列表 DoNotDelete.txt 的每一行：[(名字, 路径)]。"""
		try:
			text = codecs.open(os.path.join(WATERMELON_DATA_DIR, "DoNotDelete.txt"), 'r', encoding='utf-8').read()
		except OSError:
			return []
		return [tuple(line.split('||', 1)) for line in text.split('\n') if '||' in line]

	def _open_office_file(self, path):
		"""Open 选了一个 Word / Excel / PowerPoint 文件：加进文件下拉（已经在里面就直接切过去），并切到它。"""
		entries = self._local_file_list()
		index = next((i for i, entry in enumerate(entries) if entry[1] == path), -1)
		if index < 0:
			title = os.path.basename(path)   # 带扩展名，下拉里一眼分得出是哪种文件
			with open(os.path.join(WATERMELON_DATA_DIR, "DoNotDelete.txt"), 'a', encoding='utf-8') as f0:
				f0.write(title + '||' + path + '\n')
			self.widget0.addItems([title])
			index = self.widget0.count() - 1
		if self.widget0.currentIndex() != index:
			self.widget0.setCurrentIndex(index)   # → index_change
		if self._current_local_file_path() != path:
			self.index_change(index)

	def _export_office_copy(self, folder):
		source = self.office_panel.current_path()
		target = os.path.join(folder, os.path.basename(source))
		if os.path.abspath(target) == os.path.abspath(source):
			return   # 选的就是文件自己所在的文件夹：文件本来就在这里
		if os.path.exists(target):
			stem, extension = os.path.splitext(os.path.basename(source))
			counter = 2
			while os.path.exists(target):
				target = os.path.join(folder, '%s %d%s' % (stem, counter, extension))
				counter += 1

		def done(ok, reason, name=os.path.basename(target)):
			if ok:
				self._show_mode_toast(_tr("Saved a copy: %1").replace('%1', name))
			else:
				watermelon_alert(self, _tr("Export"), _tr('Could not save a copy of "%1": %2').replace(
					'%1', os.path.basename(source)).replace('%2', str(reason)))

		self.office_panel.copy_to(target, done)

	def _on_office_save_failed(self, path, reason):
		watermelon_alert(self, NAME, _tr('Could not save "%1": %2\n\nThe document stays open; your changes are still in it.').replace(
			'%1', os.path.basename(path)).replace('%2', str(reason)))

	def _on_office_switch_refused(self, path):
		"""切文件前存不进去：留在这份 Office 文件上（改动还在里面），下拉也拨回它。"""
		entries = self._local_file_list()
		index = next((i for i, entry in enumerate(entries) if entry[1] == path), -1)
		if index < 0:
			return
		with open(os.path.join(WATERMELON_DATA_DIR, "Current.txt"), 'w', encoding='utf-8') as f0:
			f0.write(str(index))
		self.widget0.blockSignals(True)
		self.widget0.setCurrentIndex(index)
		self.widget0.blockSignals(False)
		self.bottom.blockSignals(True)
		self.bottom.clear()
		self.bottom.blockSignals(False)
		self._sync_office_view()

	def _notes_flush_before_quit(self):
		try:
			if self.notes_mode_enabled and self.notes_dirty:
				self._notes_flush(wait_ms=8000)
		except Exception:
			logging.exception('Saving the note before quitting failed.')

	def _flush_office_before_quit(self):
		"""退出前：最后的改动存进文件（最多等十几秒）。"""
		if self.office_panel is not None:
			try:
				self.office_panel.flush_blocking()
			except Exception:
				logging.exception('Saving the Office file before quitting failed.')

	# ---------- 网页模式 ----------
	def _ensure_web_panel(self):
		"""第一次进入网页模式时才创建浏览器（不拖慢启动）。"""
		if self.web_panel is not None:
			return True
		state_dir = WATERMELON_DATA_DIR
		os.makedirs(state_dir, exist_ok=True)
		profile = QWebEngineProfile('WatermelonWebProfile')
		# 登录状态（cookies / localStorage）存盘，重启后仍是登录状态
		profile.setPersistentStoragePath(os.path.join(state_dir, 'web_profile'))
		profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
		# 输入法补发 229 按键（微软 Word 网页版里 ATOK / 中文输入法打不进字的修补，见 WEB_IME_KEYDOWN_SHIM_JS 处说明）
		_install_ime_keydown_shim(profile)
		self._web_profile = profile
		panel = WebModePanel(profile, state_dir, parent=self.qw0)
		profile.downloadRequested.connect(panel.handle_download)
		panel.setFixedWidth(self.bottom.minimumWidth() or 1235)
		panel.hide()
		layout = self.qw0.layout()
		layout.insertWidget(layout.indexOf(self.splitter2) + 1, panel)
		panel.active_url_changed.connect(self._on_web_url_changed)
		panel.active_nav_state_changed.connect(self._on_web_nav_state)
		panel.active_selection_changed.connect(self._on_web_selection)
		panel.focus_address_requested.connect(self._focus_web_address)
		panel.toast_requested.connect(self._show_mode_toast)
		panel.installEventFilter(self)   # 点击穿透的形状跟着网页区走
		if WEB_IME_DEBUG_LOG:
			self._ime_debug_filter = _ImeDebugEventFilter(panel)
			QApplication.instance().installEventFilter(self._ime_debug_filter)
		# 输入法中转（装在诊断过滤器之后 → 先于它收到事件；被中转的事件不再进网页引擎）
		self._ime_bridge = WebImeBridge(panel)
		QApplication.instance().installEventFilter(self._ime_bridge)
		self.web_panel = panel
		return True

	def toggle_web_mode(self):
		"""按一下进网页模式（编辑区整列换成网页），再按一下回到原来的本地 / Notes 模式。"""
		if not self.web_mode_enabled:
			if not self._ensure_web_panel():
				return
			self.web_mode_enabled = True
			self._web_selected_text = ''
			self.btn0_2.setEnabled(False)   # 网页模式下本地/Notes 切换和提词器不可用
			self.btn0_web.setSelected(True)
			self._sync_office_view()
			self._apply_mode_visibility()
			self.web_panel.activate()
			self._show_mode_toast(_tr("Web Mode"))
		else:
			self.web_mode_enabled = False
			self._web_selected_text = ''
			self.btn0_2.setEnabled(True)
			self.btn0_web.setSelected(False)
			self._sync_office_view()
			self._apply_mode_visibility()
			self._show_mode_toast(_tr("Notes Mode") if self.notes_mode_enabled else _tr("Local Mode"))
		self._update_word_count_label()

	def _on_web_url_changed(self, url_text):
		# 只有用户正在地址栏里打字（改过内容）时才不覆盖；单纯有焦点（比如刚开新标签）照常更新
		if self.web_address.hasFocus() and self.web_address.isModified():
			return
		self.web_address.setText(url_text)
		self.web_address.setCursorPosition(0)

	def _on_web_nav_state(self, can_back, can_forward):
		self.btn_web_back.setEnabled(bool(can_back))
		self.btn_web_forward.setEnabled(bool(can_forward))

	def _on_web_selection(self, text):
		self._web_selected_text = str(text or '')
		if self.web_mode_enabled:
			self._update_word_count_label()

	def _focus_web_address(self):
		self.web_address.setFocus()
		self.web_address.selectAll()

	def _web_address_submitted(self):
		if self.web_panel is not None:
			self.web_address.setModified(False)
			self.web_panel.navigate_active(self.web_address.text())
			self.web_panel.active_view().setFocus()

	def web_go_back(self):
		if self.web_panel is not None:
			self.web_panel.go_back()

	def web_go_forward(self):
		if self.web_panel is not None:
			self.web_panel.go_forward()

	def web_reload(self):
		if self.web_panel is not None:
			self.web_panel.reload_active()

	def web_save_to_local(self):
		self._web_save('local')

	def web_save_to_notes(self):
		self._web_save('notes')

	def _web_save(self, target):
		"""把当前网页（选中的部分，或 Google 文档/幻灯片的导出内容）存成 Markdown。"""
		if self.web_panel is None:
			return
		self.web_panel.extract_active_markdown(
			lambda title, md, error, t=target: self._on_web_content_extracted(t, title, md, error))

	def _on_web_content_extracted(self, target, title, md, error):
		if error or not str(md or '').strip():
			self._show_mode_toast(error or _tr("Nothing to save"))
			return
		if target == 'local':
			name = self._save_markdown_as_local_file(title, md)
			self._show_mode_toast(_tr("Saved to Local: %1").replace('%1', str(name)) if name else _tr("Couldn't save the file"))
			return
		note_html = watermelon_notes.markdown_to_notes_html(md)
		worker = NoteCreateWorker(self._create_note_in_folder, self.notes_current_folder or "", title or "Web Clip", note_html, self)
		worker.result.connect(self._on_web_note_created)
		worker.finished.connect(lambda w=worker: self._note_create_workers.remove(w) if w in self._note_create_workers else None)
		worker.finished.connect(worker.deleteLater)
		self._note_create_workers.append(worker)
		worker.start()

	def _on_web_note_created(self, ok, detail):
		if ok:
			self._show_mode_toast(_tr("Saved to Notes: %1").replace('%1', str(detail)))
			self._request_notes_cache_refresh()
		else:
			self._show_mode_toast(_tr("Couldn't save to Notes"))

	def _save_markdown_as_local_file(self, title, md):
		"""在数据文件夹里新建一个本地文件并加进文件列表；不切换当前文件，不动编辑器内容。"""
		try:
			app_dir = WATERMELON_DATA_DIR
			base = re.sub(r'[\\/:*?"<>|\n\r\t]+', ' ', str(title or '')).strip()[:80] or "Web Clip"
			name = base
			path = os.path.join(app_dir, name + ".md")
			counter = 2
			while os.path.exists(path):
				name = f"{base} {counter}"
				path = os.path.join(app_dir, name + ".md")
				counter += 1
			with open(path, 'w', encoding='utf-8') as f0:
				f0.write(md)
			with open(os.path.join(app_dir, "DoNotDelete.txt"), 'a', encoding='utf-8') as f0:
				f0.write(name + '||' + path + '\n')
			self.widget0.blockSignals(True)
			self.widget0.addItems([name])
			self.widget0.blockSignals(False)
			return name
		except Exception:
			logging.exception('save web clip to local failed')
			return ""

	def toggle_teleprompter(self):
		if self._office_shown() and not self._teleprompter_mode:
			return   # Office 文件没有提词器
		self._teleprompter_mode = not self._teleprompter_mode
		teleprompter_action.setChecked(self._teleprompter_mode)
		if self._teleprompter_mode:
			# 保存当前状态
			self._saved_tp_splitter1_sizes = self.splitter1.sizes()
			self._saved_tp_splitter2_sizes = self.splitter2.sizes()

			# 固定宽度容器：物理限制 splitter1 的可用空间为 250px
			# （不依赖 splitter1 的 max/minWidth，避免 QWebEngineView 原生视图撑开）
			self._tp_container = QWidget()
			self._tp_container.setFixedWidth(350)
			container_layout = QVBoxLayout(self._tp_container)
			container_layout.setContentsMargins(0, 0, 0, 0)
			container_layout.addWidget(self.splitter1)

			# 居中外层：stretch(1) + container + stretch(1)
			self._tp_wrapper = QWidget()
			wrapper_layout = QHBoxLayout(self._tp_wrapper)
			wrapper_layout.setContentsMargins(0, 0, 0, 0)
			wrapper_layout.addStretch(1)
			wrapper_layout.addWidget(self._tp_container)
			wrapper_layout.addStretch(1)

			# 插入 splitter2 第一个位置
			self.splitter2.insertWidget(0, self._tp_wrapper)

			# 高度自动跳转为 100（可通过拖拽 splitter2 手柄调整）
			total = sum(self.splitter2.sizes())
			self.splitter2.setSizes([100, max(total - 100, 50)])

			self._show_mode_toast(_tr("Teleprompter"))
			# 重新渲染内容，应用加大的行距
			self.text_change()
		else:
			# 将 splitter1 从 container 取出，放回 splitter2 第一个位置
			self.splitter2.insertWidget(0, self.splitter1)

			# 移除并删除 wrapper（container 是其子控件，会一起销毁）
			self._tp_wrapper.setParent(None)
			self._tp_wrapper.deleteLater()
			self._tp_wrapper = None
			self._tp_container = None

			# 恢复 splitter 尺寸
			self.splitter1.setSizes(self._saved_tp_splitter1_sizes)
			self.splitter2.setSizes(self._saved_tp_splitter2_sizes)

			self._show_mode_toast(_tr("Normal Mode"))
			# 重新渲染内容，恢复默认行距
			self.text_change()

	def open_notes_folder_dialog(self):
		if self.notes_folder_dialog:
			self.notes_folder_dialog.raise_()
			self.notes_folder_dialog.activateWindow()
			self.notes_folder_dialog.show()
			self.load_notes()
			return
		self.notes_folder_dialog = NotesFolderDialog()
		self.notes_folder_dialog.note_selected.connect(self.on_notes_note_selected)
		self.notes_folder_dialog.destroyed.connect(self._clear_notes_folder_dialog)
		self.notes_folder_dialog.show()
		self.notes_folder_dialog.raise_()
		self.notes_folder_dialog.activateWindow()
		self.load_notes()

	def load_notes(self):
		notes, error = _read_notes_cache(self.notes_cache_path)
		if error:
			self.on_notes_error(error)
			return
		self.on_notes_loaded(notes)

	def _clear_notes_folder_dialog(self, _obj=None):
		self.notes_folder_dialog = None

	def on_notes_loaded(self, notes):
		self.notes_data = notes
		if self.notes_folder_dialog:
			self.notes_folder_dialog.set_notes(self.notes_data)
		if not self.notes_mode_enabled:
			# 扫描结果回来前用户已切回 Local 模式：只更新列表，不选中/加载笔记，
			# 否则会把笔记内容塞进本地文件的编辑器
			self.notes_reload_pending = False
			self.notes_require_match_on_show = False
			return
		if self.notes_reload_pending:
			self.notes_reload_pending = False
			if self._select_notes_after_reload():
				self.notes_require_match_on_show = False
				return
			if self.notes_require_match_on_show and self.notes_last_title:
				self.notes_require_match_on_show = False
				self._prompt_notes_reselect(self.notes_last_folder, self.notes_last_title)
				return
		# 如果正在等待用户重新选择路径，不要重复检查
		if self.notes_awaiting_reselect:
			return
		# 如果没有选择新的文件，尝试保持之前的路径
		if self.notes_current_folder and self.notes_current_title:
			# 验证之前的路径是否仍然有效
			# （先按编号看存储里还有没有这张笔记，不用问备忘录；存储读不到才问）
			open_note = self._notes_open_note or {}
			if watermelon_notes.note_state(self.notes_current_folder, self.notes_current_title,
										   _note_id_for(self.notes_current_folder, self.notes_current_title, open_note.get("id"))) is not None:
				return
			check_html = self._read_note_html(self.notes_current_folder, self.notes_current_title, open_note.get("id"))
			if check_html is not None and check_html.strip():
				# 之前的路径有效，保持当前状态
				return
			else:
				# 之前的路径无效，锁定编辑器并提示用户
				self._set_notes_active(False)
				self._prompt_notes_reselect(self.notes_current_folder, self.notes_current_title)
				return
		self.notes_current_folder = None
		self.notes_current_title = None
		self.notes_current_list = []
		self._set_notes_new_enabled(False)
		self._set_notes_export_enabled(False)
		self.widget_notes.blockSignals(True)
		self.widget_notes.clear()
		self.widget_notes.blockSignals(False)
		self.widget_notes.setEnabled(False)
		self._set_notes_active(False)

	def _select_notes_after_reload(self):
		if not self.notes_data:
			return False
		target_title = self.notes_current_title or self.notes_pending_title
		target_folder = self.notes_current_folder or self.notes_pending_folder
		if target_title:
			best_note = None
			for note in self.notes_data:
				title = note.get("title") or "(Untitled)"
				folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
				if title == target_title:
					if target_folder and folder != target_folder:
						continue
					best_note = note
					break
			if not best_note:
				for note in self.notes_data:
					title = note.get("title") or "(Untitled)"
					if title == target_title:
						best_note = note
						break
			if best_note:
				note_folder = (best_note.get("folder") or "Unfiled").strip() or "Unfiled"
				note_title = best_note.get("title") or "(Untitled)"
				self.notes_pending_title = None
				self.notes_pending_folder = None
				self._select_note_by_folder_title(note_folder, note_title, force_reload=True)
				return True
		if self.notes_current_folder:
			current_title = self.notes_current_title
			self._select_note_by_folder_title(self.notes_current_folder, current_title, force_reload=True)
			return True
		return False

	def on_notes_error(self, message):
		self.notes_data = []
		self.notes_current_folder = None
		self.notes_current_title = None
		self.notes_current_list = []
		self.notes_reload_pending = False
		self.notes_force_reload = False
		self.notes_pending_title = None
		self.notes_pending_folder = None
		self._set_notes_new_enabled(False)
		self._set_notes_export_enabled(False)
		self.widget_notes.blockSignals(True)
		self.widget_notes.clear()
		self.widget_notes.blockSignals(False)
		self.widget_notes.setEnabled(False)
		self._set_notes_active(False)
		if self.notes_folder_dialog:
			self.notes_folder_dialog.set_notes([])
			self.notes_folder_dialog.set_status(message)

	# def on_notes_folder_selected(self, folder):
	# 	self.notes_current_title = None
	# 	self._apply_notes_folder(folder)
	# 	if self.notes_mode_enabled:
	# 		current_index = self.widget_notes.currentIndex()
	# 		if 0 <= current_index < len(self.notes_current_list):
	# 			self.notes_index_change(current_index)
	# 		else:
	# 			self.bottom.blockSignals(True)
	# 			self.bottom.clear()
	# 			self.bottom.blockSignals(False)
	# 			self.topleft.clear()
	# 			self.topright.clear()

	def on_notes_note_selected(self, note):
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		self._select_note_by_folder_title(folder, title, force_reload=True)

	def _select_note_by_folder_title(self, folder, title, force_reload=False):
		self.notes_current_folder = folder
		self.notes_current_title = title
		self._apply_notes_folder(folder, note_title=title)
		if self.notes_mode_enabled:
			current_index = self.widget_notes.currentIndex()
			if force_reload:
				self.notes_force_reload = True
			if 0 <= current_index < self.widget_notes.count():
				self.notes_index_change(current_index)
			else:
				self.bottom.blockSignals(True)
				self.bottom.clear()
				self.bottom.blockSignals(False)
				self.topleft.setHtml("", LOCAL_PAGE_BASE)
				self.topright.clear()

	def new_notes_note(self):
		if not self.notes_mode_enabled:
			return
		folder = self.notes_current_folder or ""
		now_str = datetime.now().strftime('%Y-%m-%d %H%M%S')
		title = f"Note {now_str}"
		note_md = ""
		note_html = watermelon_notes.markdown_to_notes_html(note_md)
		try:
			created_folder = self._create_note_in_folder(folder, title, note_html)
		except Exception:
			return
		if created_folder:
			folder = created_folder
		elif not folder:
			folder = "Unfiled"
		self.notes_current_folder = folder or None
		self.notes_current_title = title
		self.notes_pending_title = title
		self.notes_pending_folder = self.notes_current_folder
		new_note = {"folder": folder, "title": title, "body": note_html}
		self.notes_data.insert(0, new_note)
		try:
			_write_notes_cache(self.notes_data, self.notes_cache_path)
		except Exception:
			pass
		if folder:
			self._select_note_by_folder_title(folder, title, force_reload=True)
		notes, error = _read_notes_cache(self.notes_cache_path)
		if not error and self._note_in_cache(notes, folder, title):
			self.notes_reload_pending = True
			self.notes_force_reload = True
			self.on_notes_loaded(notes)
		else:
			self._start_notes_wait(folder, title)

	def _create_note_in_folder(self, folder, title, html):
		"""新建一张笔记；正文里的本地图片 / 文件 / 视频成为附件，位置不变。返回它所在的文件夹。"""
		return watermelon_notes.run_with_attachments(
			html, lambda final_html: self._create_note_in_folder_raw(folder, title, final_html))

	@staticmethod
	def _body_starts_with_title(html, title):
		"""正文第一行就是标题 → 新建时不再另外给笔记名（备忘录会拿第一行当名字）。两个都给的话，备忘录会在
		最上面再加一行标题（2026-11-20 Ryan：“有一个 title 就可以了”）。"""
		first = re.search(r'<(h[1-6]|div|p)\b[^>]*>(.*?)</\1>', html or '', re.S | re.I)
		if not first:
			return False
		text = html_lib.unescape(re.sub(r'<[^>]+>', '', first.group(2))).replace('\u200b', '')
		return re.sub(r'\s+', ' ', text).strip() == re.sub(r'\s+', ' ', str(title or '')).strip() != ''

	def _create_note_in_folder_raw(self, folder, title, html):
		with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".html") as f0:
			f0.write(html)
			path = f0.name
		script = r'''
		on run argv
			set targetFolder to item 1 of argv
			set targetTitle to item 2 of argv
			set filePath to item 3 of argv
			set newHTML to (do shell script "cat " & quoted form of filePath)
			tell application "Notes"
				if (item 4 of argv) is "1" then
					set noteProps to {body:newHTML}
				else
					set noteProps to {name:targetTitle, body:newHTML}
				end if
				if targetFolder is "" or targetFolder is "Unfiled" then
					set theNote to make new note with properties noteProps
				else if targetFolder contains "/" then
					set AppleScript's text item delimiters to "/"
					set parts to text items of targetFolder
					set acctName to item 1 of parts
					set folderName to ""
					if (count of parts) > 1 then
						set folderName to item 2 of parts
					end if
					set theAcct to account acctName
					if folderName is "" then
						set theNote to make new note at theAcct with properties noteProps
					else
						set theNote to make new note at folder folderName of theAcct with properties noteProps
					end if
				else
					set theFolder to missing value
					repeat with a in accounts
						if exists folder targetFolder of a then
							set theFolder to folder targetFolder of a
							exit repeat
						end if
					end repeat
					if theFolder is missing value then
						set theNote to make new note with properties noteProps
					else
						set theNote to make new note at theFolder with properties noteProps
					end if
				end if
				set f to "Unfiled"
				set accountName to ""
				try
					set c to container of theNote
					set cClass to class of c
					if cClass is folder then
						set f to name of c
						try
							set accountName to name of container of c
						end try
					else if cClass is account then
						set f to name of c
					end if
				on error
					try
						set f to name of folder of theNote
					end try
				end try
				if accountName is not "" then
					set f to accountName & "/" & f
				end if
				return f
			end tell
		end run
		'''
		result = subprocess.check_output(["osascript", "-e", script, folder, title, path,
										  "1" if self._body_starts_with_title(html, title) else "0"], text=True)
		return result.strip()

	def export_notes_file(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, _tr('Open'), home_dir)
		if fj != '':
			self.export_markdown_to(fj, self.widget_notes.currentText().strip() or "Note")

	def notes_index_change(self, index):
		if index < 0:
			return
		note = self.widget_notes.itemData(index)
		if not note:
			if index >= len(self.notes_current_list):
				return
			note = self.notes_current_list[index]
		# 换笔记之前，先把正开着的那张还没存的修改存进去
		if self._notes_open_note is not None and self._notes_open_note is not note and self.notes_dirty:
			self._notes_flush()
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		note_md, fingerprint = _load_note_markdown(folder, title, note.get("id"))
		if note_md is None:
			note_md = ""
			if self.notes_require_match_on_show:
				self.notes_require_match_on_show = False
				self._prompt_notes_reselect(folder, title)
				return
		note_key = f"{folder}/{title}"
		self.notes_force_reload = False
		self._notes_open_note = note
		self._notes_base_md, self._notes_base_fp = note_md, fingerprint
		self._notes_save_state = ''
		self._notes_conflict_snoozed = ''
		# Notes 模式没有本地源文件，这里记录“当前已加载内容”作为备份比对基线。
		self._last_notes_backup_hash[note_key] = hashlib.sha1(note_md.encode('utf-8')).hexdigest()
		self._set_notes_active(True)
		self.notes_awaiting_reselect = False  # 成功加载笔记，重置标志
		self.notes_current_title = title
		self.bottom.blockSignals(True)
		self.bottom.setPlainText(note_md)
		self.bottom.blockSignals(False)
		self._restore_notes_position(note_key)
		if not note_md:
				self.topleft.setHtml("", LOCAL_PAGE_BASE)
				self.topright.clear()
				self._set_notes_dirty(False)
				return
		self._request_async_preview_render(note_md, debounce_ms=0)
		self._set_notes_dirty(False)

	# ---------- 备忘录：自动保存、两边同时改、不轮询（2026-11-21）----------
	# Ryan：“save 就是一个自动 save 的功能”“不希望…做了一些修改然后因为读取速度不够然后没保存下来，特别是两边
	# 同时操作修改的时候。你参考 tomato 和 calendar…不要轮询”。
	# - 记住这张笔记“上次和备忘录对齐时的样子”（_notes_base_md）和那时存储的指纹（_notes_base_fp）。
	# - 停笔 2 秒 → save_notes_sync：先看存储的指纹变没变。变了 = 备忘录那边（或 iPhone）也改了 → 把
	#   原来的样子 / 我这边 / 备忘录现在 三份按段落合并（各改各的段落就都留下；改了同一段才问用哪边），再写。
	#   写在后台线程里做，写的时候可以接着打字；写完再看编辑框有没有新修改。
	# - 备忘录存储的文件一变，文件系统会通知（QFileSystemWatcher）：我这边没有没存的修改 → 直接换成新内容；
	#   有 → 留到下次保存时合并。自己写进去引起的那次通知，指纹和记下的一样，什么都不做。
	# - 写仍然经过备忘录自己（AppleScript）。直接改它的数据库不行：一张笔记的记录大部分是编辑历史、版本号和
	#   iCloud 状态，备忘录和它的同步进程内存里另有一份，绕过它们写会弄坏笔记或被 iCloud 合并回去。
	def _setup_notes_sync(self):
		self._notes_save_timer = QTimer(self)
		self._notes_save_timer.setSingleShot(True)
		self._notes_save_timer.timeout.connect(self.save_notes_sync)
		self._notes_store_timer = QTimer(self)      # 一连串文件变动只处理最后一次
		self._notes_store_timer.setSingleShot(True)
		self._notes_store_timer.setInterval(350)
		self._notes_store_timer.timeout.connect(self._on_notes_store_changed)
		self._notes_store_watcher = QFileSystemWatcher(self)
		self._notes_store_watcher.fileChanged.connect(self._notes_store_touched)
		self._notes_store_watcher.directoryChanged.connect(self._notes_store_touched)
		self._watch_notes_store()

	def _watch_notes_store(self):
		"""盯着备忘录存储的文件（库、它的写入日志、所在文件夹）。读不到存储就不盯，后台照旧定时去问备忘录。"""
		store = watermelon_notes.NOTES_STORE
		readable = watermelon_notes.list_notes_from_store() is not None
		wanted = [path for path in (os.path.dirname(store), store, store + '-wal') if os.path.exists(path)] if readable else []
		watched = set(self._notes_store_watcher.files()) | set(self._notes_store_watcher.directories())
		missing = [path for path in wanted if path not in watched]
		if missing:
			self._notes_store_watcher.addPaths(missing)
		NOTES_STORE_WATCH['on'] = bool(wanted)

	def _notes_store_touched(self, _path=''):
		self._notes_store_timer.start()

	def _on_notes_store_changed(self):
		self._watch_notes_store()        # 写入日志被换成新文件时要重新盯
		if self.notes_cache_worker:
			self.notes_cache_worker.request_refresh()   # 笔记列表（读存储，很快）
		note = self._notes_open_note
		if not self.notes_mode_enabled or not self.notes_active or note is None or self._notes_save_worker is not None:
			return
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		state = watermelon_notes.note_state(folder, title, _note_id_for(folder, title, note.get("id")))
		if state is None or not self._notes_base_fp or state[0] == self._notes_base_fp:
			return
		if self.notes_dirty:
			return        # 我这边也有没存的修改：下次保存时一起合并
		theirs, fingerprint = _load_note_markdown(folder, title, note.get("id"))
		if theirs is None:
			return
		self._notes_base_md, self._notes_base_fp = theirs, fingerprint
		if theirs != self.bottom.toPlainText():
			self._replace_notes_text(theirs)
			self._request_async_preview_render(theirs, debounce_ms=0)
		self._follow_notes_title(note, folder, self._notes_title_from_md(theirs))

	def _replace_notes_text(self, text):
		"""把编辑框换成新内容，光标和滚动位置尽量留在原处；不算“我改了”。"""
		cursor = self.bottom.textCursor()
		position, scroll = cursor.position(), self.bottom.verticalScrollBar().value()
		self.bottom.blockSignals(True)
		self.bottom.setPlainText(text)
		self.bottom.blockSignals(False)
		cursor = self.bottom.textCursor()
		cursor.setPosition(min(position, len(self.bottom.toPlainText())))
		self.bottom.setTextCursor(cursor)
		self.bottom.verticalScrollBar().setValue(scroll)

	def _follow_notes_title(self, note, folder, new_title):
		"""第一行（标题）变了：下拉里的名字、记着的当前标题跟着变，不问（按编号找笔记，改标题不会找错）。"""
		old_title = note.get("title") or "(Untitled)"
		if not new_title or new_title == old_title:
			return
		note["title"] = new_title
		if note.get("id"):
			_NOTE_ID_BY_KEY[(folder, new_title)] = str(note.get("id"))
		self.notes_current_title = new_title
		index = self.widget_notes.currentIndex()
		if index >= 0 and self.widget_notes.itemData(index) is note:
			# 共用的下拉控件没有“改某一项的名字”的方法：直接换它那一项的文字，再让它重画当前项
			items = getattr(self.widget_notes, '_items', None)
			if isinstance(items, list) and index < len(items):
				items[index] = new_title
				self.widget_notes._update_text()
		try:
			_write_notes_cache(self.notes_data, self.notes_cache_path)
		except Exception:
			pass

	def save_notes_sync(self):
		"""把正开着的笔记存进备忘录（自动保存到点、换笔记、收起、退出前都走这里）。后台写，不卡界面。"""
		note = self._notes_open_note
		if not self.notes_active or note is None:
			return
		if self._notes_save_worker is not None:
			return        # 正在写：写完会再看编辑框有没有新修改
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		note_id = _note_id_for(folder, title, note.get("id"))
		key = _note_storage_key(folder, title, note_id)
		mine = self.bottom.toPlainText()
		if mine == self._notes_base_md:
			self._notes_save_state = 'saved'
			self._set_notes_dirty(False)
			return
		if key in self._notes_autosave_off:
			self._notes_save_state = 'failed'
			self._update_word_count_label()
			return
		# 备忘录那边也改了吗？
		state = watermelon_notes.note_state(folder, title, note_id)
		if state is not None and self._notes_base_fp and state[0] != self._notes_base_fp:
			theirs, fingerprint = _load_note_markdown(folder, title, note_id)
			if theirs is not None and theirs != self._notes_base_md:
				merged, conflicts = watermelon_notes.merge_markdown(self._notes_base_md, mine, theirs)
				if conflicts:
					if mine == self._notes_conflict_snoozed:
						return        # 问过了、文字没再变：不重复问
					answer = watermelon_choice(self, _tr("Changed on Both Sides"), _tr(
						'This note was changed here and in Notes at the same time, and %1 paragraph(s) were changed on both sides. Which version of those paragraphs should be kept? Everything else from both sides is kept.'
					).replace('%1', str(conflicts)), [_tr("Keep Mine"), _tr("Keep Notes' Version"), _tr("Cancel")], _tr("Keep Mine"), escape=_tr("Cancel"))
					if answer not in (_tr("Keep Mine"), _tr("Keep Notes' Version")):
						self._notes_conflict_snoozed = mine
						self._notes_save_state = 'failed'
						self._update_word_count_label()
						return
					merged, _ = watermelon_notes.merge_markdown(self._notes_base_md, mine, theirs,
															   prefer='theirs' if answer == _tr("Keep Notes' Version") else 'mine')
				if merged != mine:
					self._replace_notes_text(merged)
					self._request_async_preview_render(merged, debounce_ms=0)
					mine = merged
			if theirs is not None:
				self._notes_base_md, self._notes_base_fp = theirs, fingerprint
			if mine == self._notes_base_md:
				self._notes_save_state = 'saved'
				self._set_notes_dirty(False)
				return
		# 只有备忘录自己做得出来的东西（手画的图、网页链接预览、#标签、@提及）：重写正文后内容还在原位，但会变成
		# 普通图片 / 普通链接 / 普通文字（没有任何写法能把它们原样写回去）→ 每张笔记第一次保存前问一次；
		# 不同意 = 这张笔记这次运行里不自动存。
		if key not in self._notes_drawing_confirmed:
			native_only = watermelon_notes.note_native_only(folder, title, note_id=note_id)
			if native_only:
				names = {'drawing': _tr('a drawing'), 'link preview': _tr('a link preview'), 'tag': _tr('a tag'), 'mention': _tr('a mention')}
				answer = watermelon_choice(self, _tr("Made in Notes"), _tr(
					'This note has %1, which only Notes itself can make. Saving from Watermelon keeps the content at its place, but a drawing becomes a picture, a link preview becomes a plain link, and tags and mentions become plain text.'
				).replace('%1', _tr(', ').join(names[kind] for kind in native_only)), [_tr("Save"), _tr("Cancel")], _tr("Save"), escape=_tr("Cancel"))
				if answer != _tr("Save"):
					self._notes_autosave_off.add(key)
					self._notes_save_state = 'failed'
					self._update_word_count_label()
					return
			self._notes_drawing_confirmed.add(key)
		self._notes_save_timer.stop()
		self._notes_save_state = 'saving'
		self._update_word_count_label()
		worker = NoteSaveWorker(folder, title, note_id, mine, self._write_note_html, self)
		worker.done.connect(lambda ok, written, fingerprint, error, n=note, w=worker: self._on_notes_saved(n, w, ok, written, fingerprint, error))
		self._notes_save_worker = worker
		worker.start()

	def _on_notes_saved(self, note, worker, ok, written, fingerprint, error):
		if worker is self._notes_save_worker:
			self._notes_save_worker = None
		worker.wait(2000)
		worker.deleteLater()
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		if not ok:
			logging.warning('Saving the note to Notes failed: %s', error)
			if note is self._notes_open_note:
				self._notes_save_state = 'failed'
				self._update_word_count_label()
				if 'NOT_FOUND' in str(error):
					self._set_notes_active(False)
					self._prompt_notes_reselect(folder, title)
			return
		key = _note_storage_key(folder, title, note.get("id"))
		if fingerprint:
			NOTE_MEMORY.remember(key, '', written, fingerprint=fingerprint)
		new_title = self._notes_title_from_md(written)
		final_title = new_title or title
		self._backup_notes_mode_if_changed(f"{folder}/{final_title}", final_title, written)
		if note is not self._notes_open_note:
			note["title"] = final_title
			return        # 存的是刚才那张（换笔记前补存的）
		self._notes_base_md, self._notes_base_fp = written, fingerprint
		self._follow_notes_title(note, folder, new_title)
		if self.bottom.toPlainText() != written:
			self._notes_save_state = ''
			self._set_notes_dirty(True)       # 写的时候又打了字：再存一次
		else:
			self._notes_save_state = 'saved'
			self._set_notes_dirty(False)

	def _notes_flush(self, wait_ms=12000):
		"""现在就存，并等它写完（换笔记、换模式、收起、退出之前）。最多等 wait_ms。"""
		if not self.notes_active or self._notes_open_note is None:
			return
		deadline = time.time() + wait_ms / 1000.0
		for _ in range(3):        # 写的过程中又有修改的话再来一次
			if self._notes_save_worker is None:
				if not self.notes_dirty and self.bottom.toPlainText() == self._notes_base_md:
					return
				self.save_notes_sync()
				if self._notes_save_worker is None:
					return        # 不用写，或者被问住了 / 不自动存
			loop = QEventLoop()
			worker = self._notes_save_worker
			worker.finished.connect(loop.quit)
			QTimer.singleShot(max(1, int((deadline - time.time()) * 1000)), loop.quit)
			if worker.isRunning():
				loop.exec()
			QApplication.processEvents()
			if time.time() >= deadline:
				return

	def open_current_note_in_notes(self):
		"""在备忘录里打开正开着的这张笔记（先把没存的存进去）。"""
		note = self._notes_open_note
		if note is None:
			return
		self._notes_flush()
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		script = _NOTE_LOOKUP_HANDLERS + """
on run argv
	set targetNote to my findNoteWithId(item 3 of argv, item 1 of argv, item 2 of argv)
	if targetNote is missing value then return
	tell application "Notes"
		show targetNote
		activate
	end tell
end run
"""
		subprocess.Popen(["osascript", "-e", script, folder, title, _note_id_for(folder, title, note.get("id"))],
						 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	def _write_note_html(self, folder, title, html, note_id=None):
		def write(final_html):
			with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".html") as f0:
				f0.write(final_html)
				path = f0.name
			try:
				subprocess.check_call(["osascript", "-e", _NOTE_WRITE_SCRIPT, folder, title, path, _note_id_for(folder, title, note_id)])
			finally:
				try:
					os.remove(path)
				except OSError:
					pass
		# 正文里的本地图片 / 文件 / 视频先放到备忘录读得到的临时磁盘上，写完由后台卸掉
		watermelon_notes.run_with_attachments(html, write)

	def export_file(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, _tr('Open'), home_dir)
		if fj != '' and self._office_shown():
			self._export_office_copy(fj)   # Office 文件：把这份文件另存一份副本到选的文件夹
			return
		if fj != '':
			self.export_markdown_to(fj, self.widget0.currentText())

	def export_markdown_to(self, fj, title):
		"""Export 选好文件夹以后做的事（工具也走这里）：正文一份、加粗阅读版一份。返回写出的两个文件。"""
		text_1 = self.bottom.toPlainText()
		tarname = title + ".md"
		fulldir = os.path.join(fj, tarname)
		with open(fulldir, 'w', encoding='utf-8') as f1:
			f1.write(text_1)

		text_2 = self.bottom.toPlainText()
		endbio = self.addb2(text_2.replace('*', ''))
		tarname2 = title + "_bionic.md"
		fulldirw = os.path.join(fj, tarname2)
		with open(fulldirw, 'w', encoding='utf-8') as f1:
			f1.write(endbio)
		return [fulldir, fulldirw]

	def clear_all(self):
		if is_office_path(self._current_local_file_path() or ''):
			return   # Office 文件不清空（按钮这时是灰的）
		self._set_notes_active(False)
		w3.widget0.currentIndexChanged.disconnect(w3.index_change)
		w3.bottom.textChanged.disconnect(w3.text_change)

		self.bottom.clear()
		self.topleft.setHtml("", LOCAL_PAGE_BASE)
		self.topright.clear()

		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)

		paths = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = paths.split('\n')
		while '' in pathslist:
			pathslist.remove('')

		self.widget0.setCurrentIndex(0)
		with open(fulldir4, 'w', encoding='utf-8') as f0:
			f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			self.bottom.setText(previewtext)
			self._request_async_preview_render(previewtext, debounce_ms=0)

		w3.widget0.currentIndexChanged.connect(w3.index_change)
		w3.bottom.textChanged.connect(w3.text_change)

	def open_file_menu(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getOpenFileName(self, _tr("Open File"), home_dir, _tr("Markdown Files (*.md)"))
		if fj[0] != '':
			str_fj = ''.join(fj)
			str_fj = str_fj.replace('Markdown Files (*.md)', '')
			text_open = codecs.open(str_fj, 'r', encoding='utf-8').read()
			endbio = self.addb2(text_open.replace('*', ''))
			new_str_fj = str_fj.replace('.md', '_bionic.md')
			with open(new_str_fj, 'w', encoding='utf-8') as f0:
				f0.write(endbio)

	def is_contain_english(self, str0):  # 判断是否包含英文字母
		import re
		return bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', str0))

	def is_contain_chinese(self, check_str):  # 判断是否包含中文字
		for ch in check_str:
			if u'\u4e00' <= ch <= u'\u9fff':
				return True
		return False

	def is_contain_num(self, str0):  # 判断是否包含数字
		return bool(re.search('[0-9０-９]', str0))

	def is_contain_symbol(self, keyword):
		if re.search(r"\W", keyword):
			return True
		else:
			return False

	def find_this(self, q, i):
		result = q[i]
		return result

	def find_next(self, q, i):
		result = q[i + 1]
		return result

	def addb(self):
		a = subprocess.check_output('pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
		if a != None:
			a = str(a)
			aj = jieba.cut(a, cut_all=False)
			paj = '/'.join(aj)
			saj = paj.split('/')

			for i in range(len(saj)):
				if self.is_contain_english(str(saj[i])) or self.is_contain_chinese(str(saj[i])) or self.is_contain_num(str(saj[i])):
					if len(saj[i]) == 1:
						saj[i] = '**' + saj[i] + '**'
						i = i + 1
						continue
					if len(saj[i]) >= 2:
						if 'ing' in saj[i]:
							saj[i] = saj[i].replace('ing', '**ing')
							saj[i] = saj[i].replace('**ing**ing', 'ing**ing')
							laj = list(saj[i])
							laj.insert(0, '**')
							saj[i] = ''.join(laj)
							i = i + 1
							continue
						else:
							if len(saj[i]) % 2 == 0:
								laj = list(saj[i])
								uu = len(saj[i]) / 2
								laj.insert(int(uu), '**')
								laj.insert(0, '**')
								saj[i] = ''.join(laj)
								i = i + 1
								continue
							if len(saj[i]) % 2 != 0:
								laj = list(saj[i])
								laj.insert(0, '**')
								uu = len(saj[i]) + 1
								laj.insert(int(uu / 2) + 1, '**')
								saj[i] = ''.join(laj)
								i = i + 1
								continue

			esj = ''.join(saj)

			i = 0
			while i <= len(esj) - 1:
				if esj[i] == '¥' and not self.is_contain_symbol(str(esj[i - 1])):
					esj = list(esj)
					esj.insert(i, ' ')
					esj = ''.join(esj)
					i = i + 2
					continue
				if esj[i] == '$' and not self.is_contain_symbol(str(esj[i - 1])):
					esj = list(esj)
					esj.insert(i, ' ')
					esj = ''.join(esj)
					i = i + 2
					continue
				if esj[i] == "%":
					if esj[i - 1] == ' ':
						esj = list(esj)
						del esj[i - 1]
						esj = ''.join(esj)
						i = i - 1
						continue
					else:
						esj = list(esj)
						esj.insert(i + 1, ' ')
						esj = ''.join(esj)
						i = i + 2
						continue
				if esj[i] == "°":
					if esj[i - 1] == ' ':
						esj = list(esj)
						del esj[i - 1]
						esj = ''.join(esj)
						i = i - 1
						continue
					else:
						esj = list(esj)
						esj.insert(i + 1, ' ')
						esj = ''.join(esj)
						i = i + 2
						continue
				else:
					i = i + 1
					continue

			i = 0
			while i >= 0 and i < len(esj) - 1:
				if self.is_contain_chinese(str(self.find_this(esj, i))) and self.is_contain_english(str(self.find_next(esj, i))):  # 从中文转英文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_this(esj, i))) and self.is_contain_num(str(self.find_next(esj, i))):  # 从中文转数字
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(esj, i))) and self.is_contain_num(str(self.find_this(esj, i))):  # 从数字转中文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_this(esj, i))) and self.is_contain_english(str(self.find_next(esj, i))):  # 从数字转英文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_next(esj, i))) and self.is_contain_english(str(self.find_this(esj, i))):  # 从英文转数字
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(esj, i))) and self.is_contain_english(str(self.find_this(esj, i))):  # 从英文转中文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				else:
					i = i + 1
					continue

			# 清除连续空格
			esj = esj.replace('  ', ' ')
			esj = esj.replace('****', '')

			ResultEnd = str(esj).encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))
		else:
			ResultEnd = _tr('The clipboard is empty.')
			ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))

	def addb2(self, a):
		if a != None:
			a = str(a)
			aj = jieba.cut(a, cut_all=False)
			paj = '/'.join(aj)
			saj = paj.split('/')

			for i in range(len(saj)):
				if self.is_contain_english(str(saj[i])) or self.is_contain_chinese(str(saj[i])) or self.is_contain_num(str(saj[i])):
					if len(saj[i]) == 1:
						saj[i] = '**' + saj[i] + '**'
						i = i + 1
						continue
					if len(saj[i]) >= 2:
						if 'ing' in saj[i]:
							saj[i] = saj[i].replace('ing', '**ing')
							saj[i] = saj[i].replace('**ing**ing', 'ing**ing')
							laj = list(saj[i])
							laj.insert(0, '**')
							saj[i] = ''.join(laj)
							i = i + 1
							continue
						else:
							if len(saj[i]) % 2 == 0:
								laj = list(saj[i])
								uu = len(saj[i]) / 2
								laj.insert(int(uu), '**')
								laj.insert(0, '**')
								saj[i] = ''.join(laj)
								i = i + 1
								continue
							if len(saj[i]) % 2 != 0:
								laj = list(saj[i])
								laj.insert(0, '**')
								uu = len(saj[i]) + 1
								laj.insert(int(uu / 2) + 1, '**')
								saj[i] = ''.join(laj)
								i = i + 1
								continue

			esj = ''.join(saj)

			i = 0
			while i <= len(esj) - 1:
				if esj[i] == '¥' and not self.is_contain_symbol(str(esj[i - 1])):
					esj = list(esj)
					esj.insert(i, ' ')
					esj = ''.join(esj)
					i = i + 2
					continue
				if esj[i] == '$' and not self.is_contain_symbol(str(esj[i - 1])):
					esj = list(esj)
					esj.insert(i, ' ')
					esj = ''.join(esj)
					i = i + 2
					continue
				if esj[i] == "%":
					if esj[i - 1] == ' ':
						esj = list(esj)
						del esj[i - 1]
						esj = ''.join(esj)
						i = i - 1
						continue
					else:
						esj = list(esj)
						esj.insert(i + 1, ' ')
						esj = ''.join(esj)
						i = i + 2
						continue
				if esj[i] == "°":
					if esj[i - 1] == ' ':
						esj = list(esj)
						del esj[i - 1]
						esj = ''.join(esj)
						i = i - 1
						continue
					else:
						esj = list(esj)
						esj.insert(i + 1, ' ')
						esj = ''.join(esj)
						i = i + 2
						continue
				else:
					i = i + 1
					continue

			i = 0
			while i >= 0 and i < len(esj) - 1:
				if self.is_contain_chinese(str(self.find_this(esj, i))) and self.is_contain_english(str(self.find_next(esj, i))):  # 从中文转英文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_this(esj, i))) and self.is_contain_num(str(self.find_next(esj, i))):  # 从中文转数字
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(esj, i))) and self.is_contain_num(str(self.find_this(esj, i))):  # 从数字转中文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_this(esj, i))) and self.is_contain_english(str(self.find_next(esj, i))):  # 从数字转英文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_next(esj, i))) and self.is_contain_english(str(self.find_this(esj, i))):  # 从英文转数字
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(esj, i))) and self.is_contain_english(str(self.find_this(esj, i))):  # 从英文转中文
					esj = list(esj)
					esj.insert(i + 1, ' ')
					esj = ''.join(esj)
					i = i + 1
					continue
				else:
					i = i + 1
					continue

			# 清除连续空格
			esj = esj.replace('  ', ' ')
			esj = esj.replace('****', '')

			return esj
		else:
			ResultEnd = _tr('The clipboard is empty.')
			ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))


	def remb(self):
		a = subprocess.check_output('pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
		if a != None:
			zui = a.replace('*', '')

			i = 0
			while i <= len(zui) - 1:
				if zui[i] == '¥' and not self.is_contain_symbol(str(zui[i - 1])):
					zui = list(zui)
					zui.insert(i, ' ')
					zui = ''.join(zui)
					i = i + 2
					continue
				if zui[i] == '$' and not self.is_contain_symbol(str(zui[i - 1])):
					zui = list(zui)
					zui.insert(i, ' ')
					zui = ''.join(zui)
					i = i + 2
					continue
				if zui[i] == "%":
					if zui[i - 1] == ' ':
						zui = list(zui)
						del zui[i - 1]
						zui = ''.join(zui)
						i = i - 1
						continue
					else:
						zui = list(zui)
						zui.insert(i + 1, ' ')
						zui = ''.join(zui)
						i = i + 2
						continue
				if zui[i] == "°":
					if zui[i - 1] == ' ':
						zui = list(zui)
						del zui[i - 1]
						zui = ''.join(zui)
						i = i - 1
						continue
					else:
						zui = list(zui)
						zui.insert(i + 1, ' ')
						zui = ''.join(zui)
						i = i + 2
						continue
				else:
					i = i + 1
					continue

			i = 0
			while i >= 0 and i < len(zui) - 1:
				if self.is_contain_chinese(str(self.find_this(zui, i))) and self.is_contain_english(str(self.find_next(zui, i))):  # 从中文转英文
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_this(zui, i))) and self.is_contain_num(str(self.find_next(zui, i))):  # 从中文转数字
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(zui, i))) and self.is_contain_num(str(self.find_this(zui, i))):  # 从数字转中文
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_this(zui, i))) and self.is_contain_english(str(self.find_next(zui, i))):  # 从数字转英文
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				if self.is_contain_num(str(self.find_next(zui, i))) and self.is_contain_english(str(self.find_this(zui, i))):  # 从英文转数字
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				if self.is_contain_chinese(str(self.find_next(zui, i))) and self.is_contain_english(str(self.find_this(zui, i))):  # 从英文转中文
					zui = list(zui)
					zui.insert(i + 1, ' ')
					zui = ''.join(zui)
					i = i + 1
					continue
				else:
					i = i + 1
					continue

			# 清除连续空格
			zui = zui.replace('  ', ' ')
			ResultEnd = str(zui).encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))
		else:
			ResultEnd = _tr('The clipboard is empty.')
			ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))

	def md2html(self, mdstr, pre_rendered_html=None):
		"""预览页。公式和美元符号分开判断、新的写法（==高亮==、任务清单、“+ ”短横列表）、统一的样式都在
		markdown_preview.py（和 Tomato / Strawberry 共用的一份；公式那部分是 Broccoli 的原样代码）。"""
		body = markdown_preview.render_markdown_body(mdstr) if pre_rendered_html is None else pre_rendered_html
		font_family = getattr(self, "_current_font_family", None) or self._resolve_font_family()
		font_size = getattr(self, "_current_font_size", None) or self._read_font_size()
		bg_color = getattr(self, "_current_bg_color", "#FFFFFF")
		dark = is_dark_theme(app)
		text_color = '#FFFFFF' if dark else '#000000'
		extra_css = '    body { line-height: 2.0 !important; }' if getattr(self, '_teleprompter_mode', False) else ''
		return markdown_preview.preview_page(body, font_family=font_family, font_size=font_size, background=bg_color,
											 text_color=text_color, dark=dark, extra_css=extra_css)

class window4(QWidget):  # Customization settings
	def __init__(self):
		super().__init__()
		self.init_ui()

	def init_ui(self):
		# 样式书 5.10「设置」：原来就是自己带关闭钮的独立窗口 → 系统红绿灯 + 窗口玻璃
		self.setUpMainWindow()
		make_native_glass_window(self)
		self.setFixedSize(640, 550)
		self.center()
		self.setWindowTitle(_tr('Settings'))
		self.setFocus()

	def setUpMainWindow(self):
		wid0 = QWidget()
		lbl0 = QLabel(_tr("<h2>Manage recent files</h2>"), self)
		font = PyQt6.QtGui.QFont()
		font.setBold(True)
		lbl0.setFont(font)
		b40 = QHBoxLayout()
		b40.setContentsMargins(0, 0, 0, 0)
		b40.addStretch()
		b40.addWidget(lbl0)
		b40.addStretch()
		wid0.setLayout(b40)

		wid1 = QWidget()
		self.text_feed = QListWidget(self)
		self.text_feed.setFixedWidth(550)
		# 上面多了 40 高的标题栏；后来又加了「Lecture cards language」一行，内容总高变成 566 > 550，窗口把
		# 列表的下半截（圆角和底边）裁掉了（Ryan 2026-11-25：“这个表单组件都无法显示完全”）→ 列表再矮 26，窗口仍是 640 × 550
		self.text_feed.setFixedHeight(284)
		# 一行放不下时中间用 … 截断，名字和路径末尾（文件名）都看得到，不再被右边裁掉
		self.text_feed.setTextElideMode(Qt.TextElideMode.ElideMiddle)
		self.text_feed.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.text_feed.itemSelectionChanged.connect(self.item_click)
		b41 = QHBoxLayout()
		b41.setContentsMargins(0, 0, 0, 0)
		b41.addWidget(self.text_feed)
		wid1.setLayout(b41)

		wid11 = QWidget()
		self.btn4_1 = WhiteButton(_tr('Delete'), self)
		# self.btn4_1.setFixedHeight(20)
		self.btn4_1.setFixedWidth(250)
		self.btn4_1.setVisible(False)
		self.btn4_1.clicked.connect(self.delete_item)
		btn4_11 = WhiteButton(_tr('Save'), self)
		btn4_11.clicked.connect(self.SaveFeed)
		# btn4_11.setFixedHeight(20)
		btn4_11.setFixedWidth(250)
		b411 = QHBoxLayout()
		b411.setContentsMargins(0, 8, 0, 8)
		# b411.addStretch()
		b411.addWidget(self.btn4_1)
		b411.addWidget(btn4_11)
		# b411.addStretch()
		wid11.setLayout(b411)

		self.checkBox0 = QCheckBox(_tr('Automatically scroll simultaneously'), self)
		self.checkBox0.setChecked(True)
		self.checkBox0.clicked.connect(self.auto_scroll)

		self.checkBox_top = QCheckBox(_tr('Always on top'), self)
		self.checkBox_top.setChecked(w3.is_always_on_top())
		self.checkBox_top.clicked.connect(self.toggle_on_top)

		self.checkBox_eye_care = QCheckBox(_tr('Eye care mode'), self)
		# 读取用户偏好设置（默认是白色，勾选变护眼色）
		bg_pref_file = SettingsPath + 'bg_color.txt'
		if os.path.exists(bg_pref_file):
			bg_pref = codecs.open(bg_pref_file, 'r', encoding='utf-8').read().strip()
			self.checkBox_eye_care.setChecked(bg_pref == 'cream')
		else:
			self.checkBox_eye_care.setChecked(False)
		self.checkBox_eye_care.clicked.connect(self.toggle_bg_color)

		self.widget1 = DropdownButton(self, compact_light=True)   # 紧凑灰色下拉，弹出的是系统菜单（样式书 5.2）
		self.widget1.setFixedWidth(120)   # 这一行还有三个勾选框：下拉定宽，字体名放不下用 …
		self.widget1.addItems([_tr('Last used'), _tr('Default font')])
		font_manager = matplotlib.font_manager.FontManager()
		font_list = [font.name for font in font_manager.ttflist]
		unique_font_names = list(set([font.split(",")[0] for font in font_list if not font.startswith(".")]))
		unique_font_names.sort()
		self.widget1.addItems(unique_font_names)
		self.widget1.setCurrentIndex(0)
		self.widget1.currentIndexChanged.connect(self.font_change)

		wid3 = QWidget()
		b43 = QHBoxLayout()
		b43.setContentsMargins(0, 0, 0, 0)
		b43.addWidget(self.checkBox0)
		b43.addWidget(self.checkBox_top)
		b43.addWidget(self.checkBox_eye_care)
		b43.addWidget(self.widget1)
		wid3.setLayout(b43)

		# 听课模式的卡片用什么语言写（Ryan 2026-11-21：“设置里选目标笔记语言”）
		lecture_settings = watermelon_lecture.LectureSettings(SettingsPath + 'lecture.json')
		lbl_lecture = QLabel(_tr('Lecture cards language: '), self)
		self.widget_lecture_language = DropdownButton(self, compact_light=True)
		self.widget_lecture_language.setFixedWidth(160)
		self.widget_lecture_language.addItems([watermelon_lecture.language_label(code) for code, _name in watermelon_lecture.LANGUAGES])
		codes = [code for code, _name in watermelon_lecture.LANGUAGES]
		self.widget_lecture_language.setCurrentIndex(codes.index(lecture_settings.get('language')) if lecture_settings.get('language') in codes else 0)
		self.widget_lecture_language.currentIndexChanged.connect(self.lecture_language_change)
		wid_lecture = QWidget()
		b44 = QHBoxLayout()
		b44.setContentsMargins(0, 0, 0, 0)
		b44.addWidget(lbl_lecture)
		b44.addWidget(self.widget_lecture_language)
		b44.addStretch(1)
		wid_lecture.setLayout(b44)

		lbl1 = QLabel(_tr("Font size: "), self)
		sld = QSlider(Qt.Orientation.Horizontal, self)
		sld.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		sld.setRange(14, 50)
		dfontsize = int(codecs.open(SettingsPath + 'fs.txt', 'r', encoding='utf-8').read())
		sld.setValue(dfontsize)
		font_family = codecs.open(SettingsPath + 'lastused.txt', 'r', encoding='utf-8').read()
		if font_family == '0':
			font_family = default_font_family()
		w3.set_textedit_font(dfontsize, font_family)
		sld.valueChanged[int].connect(self.value_change)
		self.lbl2 = QLabel(str(dfontsize) + " ", self)
		wid2 = QWidget()
		b42 = QHBoxLayout()
		b42.setContentsMargins(0, 0, 0, 0)
		b42.addWidget(lbl1)
		b42.addWidget(self.lbl2)
		b42.addWidget(sld)
		wid2.setLayout(b42)

		main_h_box = QVBoxLayout()
		main_h_box.addWidget(wid0)
		main_h_box.addWidget(wid1)
		main_h_box.addWidget(wid11)
		main_h_box.addWidget(wid3)
		main_h_box.addWidget(wid_lecture)
		main_h_box.addWidget(wid2)
		# main_h_box.addStretch()
		self.setLayout(main_h_box)

		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		tarname3 = "Note 001.md"
		fulldir3 = os.path.join(fulldir1, tarname3)
		if not os.path.exists(fulldir3):
			with open(fulldir3, 'a', encoding='utf-8') as f0:
				f0.write('')
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		if not os.path.exists(fulldir2):
			with open(fulldir2, 'a', encoding='utf-8') as f0:
				f0.write('Note 001||' + fulldir3 + '\n')
		exsfeeds = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = exsfeeds.split('\n')
		while '' in pathslist:
			pathslist.remove('')
		self.text_feed.clear()
		self.text_feed.addItems(pathslist)

	def load_font(self, font_path):
		# 加载本地字体
		font_id = QFontDatabase.addApplicationFont(font_path)
		if font_id == -1:
			raise Exception(_tr("Font failed to load! Check the font path."))
		return QFontDatabase.applicationFontFamilies(font_id)[0]

	def item_click(self):
		selected_items = self.text_feed.selectedItems()  # 获取已选择的项
		if len(selected_items) > 0:
			self.btn4_1.setVisible(True)
		else:
			self.btn4_1.setVisible(False)

	def delete_item(self):
		selected_items = self.text_feed.selectedItems()
		if len(selected_items) > 0:
			index = 0
			text = ''
			for item in selected_items:
				index = self.text_feed.row(item)  # 获取选中项的索引
				text = item.text()
			output_list = []
			for i in range(self.text_feed.count()):
				output_list.append(self.text_feed.item(i).text())
			while '' in output_list:
				output_list.remove('')
			if index != 0 and text != '' and 'Note 001' not in text:
				deletelist = []
				deletelist.append(output_list[index])
				output_list.remove(deletelist[0])
				#set show
				self.text_feed.clear()
				self.text_feed.addItems(output_list)

	def SaveFeed(self):
		w3.widget0.currentIndexChanged.disconnect(w3.index_change)
		w3.bottom.textChanged.disconnect(w3.text_change)
		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		tarname3 = "Note 001.md"
		fulldir3 = os.path.join(fulldir1, tarname3)
		if not os.path.exists(fulldir3):
			with open(fulldir3, 'a', encoding='utf-8') as f0:
				f0.write('')
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		tarname4 = "Current.txt"
		fulldir4 = os.path.join(fulldir1, tarname4)

		output_list = []
		for i in range(self.text_feed.count()):
			output_list.append(self.text_feed.item(i).text())
		part1 = '\n'.join(output_list) + '\n'
		if part1 != '':
			pathslist = part1.split('\n')
			while '' in pathslist:
				pathslist.remove('')
			if "Note 001" not in pathslist[0]:
				with open(fulldir2, 'w', encoding='utf-8') as f0:
					f0.write('Note 001||' + fulldir3 + '\n')
				with open(fulldir2, 'a', encoding='utf-8') as f0:
					f0.write(part1)
			if "Note 001" in pathslist[0]:
				with open(fulldir2, 'w', encoding='utf-8') as f0:
					f0.write(part1)
			w3.widget0.clear()
			namelist = []
			for i in range(len(pathslist)):
				namelist.append(pathslist[i].split('||')[0])
			w3.widget0.addItems(namelist)
			w3.widget0.currentIndexChanged.connect(w3.index_change)
			w3.widget0.setCurrentIndex(0)
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			w3.bottom.setText(previewtext)
			endhtml = w3.md2html(previewtext)
			w3.topleft.setHtml(endhtml, LOCAL_PAGE_BASE)
			endbio = w3.addb2(previewtext.replace('*', ''))
			endhtmlbio = w3.md2html(endbio)
			w3.topright.setHtml(endhtmlbio)
			w3.bottom.textChanged.connect(w3.text_change)
		if part1 == '':
			w3.widget0.currentIndexChanged.connect(w3.index_change)
			w3.widget0.setCurrentIndex(0)
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = fulldir3
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			w3.bottom.setText(previewtext)
			endhtml = w3.md2html(previewtext)
			w3.topleft.setHtml(endhtml, LOCAL_PAGE_BASE)
			endbio = w3.addb2(previewtext.replace('*', ''))
			endhtmlbio = w3.md2html(endbio)
			w3.topright.setHtml(endhtmlbio)
			w3.bottom.textChanged.connect(w3.text_change)
		w3._sync_office_view()
		self.close()

	def auto_scroll(self):
		w3.scrollbar = w3.bottom.verticalScrollBar()
		if self.checkBox0.isChecked():
			w3.scrollbar.valueChanged.connect(w3.scrollchanged)
		if not self.checkBox0.isChecked():
			w3.scrollbar.valueChanged.disconnect(w3.scrollchanged)

	def toggle_on_top(self):
		w3.set_always_on_top(self.checkBox_top.isChecked())

	def toggle_bg_color(self):
		use_eye_care = self.checkBox_eye_care.isChecked()
		pref = 'cream' if use_eye_care else 'white'
		bg_color = _resolve_bg_color(pref, is_dark_theme(app))
		# 保存用户偏好
		with open(SettingsPath + 'bg_color.txt', 'w', encoding='utf-8') as f0:
			f0.write(pref)
		# 更新w3中的组件背景颜色
		w3.set_bg_color(bg_color)

	def value_change(self, value):
		self.lbl2.setText(str(value))
		self.lbl2.adjustSize()
		targetfont = self.widget1.currentText()
		if targetfont == _tr('Last used'):
			targetfont = codecs.open(SettingsPath + 'lastused.txt', 'r', encoding='utf-8').read()
			if targetfont == '0':
				targetfont = default_font_family()
		if targetfont == _tr('Default font'):
			targetfont = default_font_family()
		w3.set_textedit_font(value, targetfont)
		with open(SettingsPath + 'fs.txt', 'w', encoding='utf-8') as f0:
			f0.write(str(value))

	def lecture_language_change(self, i):
		codes = [code for code, _name in watermelon_lecture.LANGUAGES]
		code = codes[i] if 0 <= i < len(codes) else ''
		watermelon_lecture.LectureSettings(SettingsPath + 'lecture.json').set('language', code)
		if w3.lecture_session is not None:
			w3.lecture_session.settings.set('language', code)

	def font_change(self, i):
		if i == 0:
			targetsize = int(self.lbl2.text())
			targetfont = codecs.open(SettingsPath + 'lastused.txt', 'r', encoding='utf-8').read()
			if targetfont == '0':
				targetfont = default_font_family()
			w3.set_textedit_font(targetsize, targetfont)
		if i == 1:
			targetsize = int(self.lbl2.text())
			targetfont = default_font_family()
			w3.set_textedit_font(targetsize, targetfont)
			with open(SettingsPath + 'lastused.txt', 'w', encoding='utf-8') as f0:
				f0.write('0')
		if i != 0 and i != 1:
			targetsize = int(self.lbl2.text())
			targetfont = self.widget1.itemText(i)
			w3.set_textedit_font(targetsize, targetfont)
			with open(SettingsPath + 'lastused.txt', 'w', encoding='utf-8') as f0:
				f0.write(targetfont)

	def activate(self):  # 设置窗口显示
		self.show()
		self.btn4_1.setVisible(False)
		home_dir = str(Path.home())
		fulldir1 = WATERMELON_DATA_DIR
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)
		tarname2 = "DoNotDelete.txt"
		fulldir2 = os.path.join(fulldir1, tarname2)
		if not os.path.exists(fulldir2):
			with open(fulldir2, 'a', encoding='utf-8') as f0:
				f0.write('')
		exsfeeds = codecs.open(fulldir2, 'r', encoding='utf-8').read()
		pathslist = exsfeeds.split('\n')
		while '' in pathslist:
			pathslist.remove('')
		self.text_feed.clear()
		self.text_feed.addItems(pathslist)

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def keyPressEvent(self, e):  # 当页面显示的时候，按下esc键可关闭窗口
		if e.key() == Qt.Key.Key_Escape.value:
			self.close()

	def cancel(self):  # 设置取消键的功能
		self.close()


style_sheet_ori = '''
	QTabWidget::pane {
		border: 1px solid #ECECEC;
		background: #ECECEC;
		border-radius: 9px;
}
	QWidget#Main {
		border: 1px solid #ECECEC;
		background: #ECECEC;
		border-radius: 9px;
}
	QPushButton{
		border: 1px outset grey;
		background-color: #FFFFFF;
		border-radius: 4px;
		padding: 1px;
		color: #000000
}
	QPushButton:pressed{
		border: 1px outset grey;
		background-color: #0085FF;
		border-radius: 4px;
		padding: 1px;
		color: #FFFFFF
}
	QPlainTextEdit{
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #FFFFFF;
		color: #000000;
		font: 14pt Times New Roman;
}
	QPlainTextEdit#edit{
		border: 1px solid grey;  
		border-radius:4px;
		padding: 1px 5px 1px 3px; 
		background-clip: border;
		background-color: #FFFFFF;
		color: rgb(113, 113, 113);
		font: 14pt Helvetica;
}
	QLineEdit{
		border: 1px solid #D9D9DE;
		border-radius: 6px;
		background-color: #FFFFFF;
		color: #20242B;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px;
		padding: 0px 4px;
		selection-background-color: #DCEAFB;
		selection-color: #20242B;
}
	QCheckBox{
		color: #20242B;
		font-size: 13px;
}
	QTextEdit{
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #FFFFFF;
		color: #000000;
		font: 14pt Times New Roman;
}
	QFrame#webFrame{
		border: 1px solid grey;
		border-radius:4px;
		padding: 0px;
		background-clip: border;
		background-color: #FFFFFF;
}
	QWebEngineView{
		border: 0px;
}
	QListWidget{
		border: 1px solid #ECECEC;
		border-radius: 14px;
		padding: 6px;
		background-color: #FFFFFF;
		color: #20242B;
		font: 14pt Times New Roman;
		outline: none;
}
	QListWidget::item{
		border-radius: 7px;
		padding: 3px 6px;
}
	QListWidget::item:selected{
		background: #DCEAFB;
		color: #20242B;
}
'''

style_sheet_dark = '''
	QTabWidget::pane {
		border: 1px solid #2D2D2D;
		background: #2D2D2D;
		border-radius: 9px;
}
	QWidget#Main {
		border: 1px solid #2D2D2D;
		background: #2D2D2D;
		border-radius: 9px;
}
	QPushButton{
		border: 1px outset grey;
		background-color: #3A3A3A;
		border-radius: 4px;
		padding: 1px;
		color: #FFFFFF
}
	QPushButton:pressed{
		border: 1px outset grey;
		background-color: #0085FF;
		border-radius: 4px;
		padding: 1px;
		color: #FFFFFF
}
	QPlainTextEdit{
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #3A3A3A;
		color: #FFFFFF;
		font: 14pt Times New Roman;
}
	QPlainTextEdit#edit{
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #3A3A3A;
		color: #CCCCCC;
		font: 14pt Helvetica;
}
	QLineEdit{
		border: 1px solid #4A4B4F;
		border-radius: 6px;
		background-color: #3A3A3A;
		color: #F2F2F7;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px;
		padding: 0px 4px;
		selection-background-color: #2E5C91;
		selection-color: #FFFFFF;
}
	QCheckBox{
		color: #F2F2F7;
		font-size: 13px;
}
	QTextEdit{
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #3A3A3A;
		color: #FFFFFF;
		font: 14pt Times New Roman;
}
	QFrame#webFrame{
		border: 1px solid grey;
		border-radius:4px;
		padding: 0px;
		background-clip: border;
		background-color: #3A3A3A;
}
	QWebEngineView{
		border: 0px;
}
	QListWidget{
		border: 1px solid #4A4B4F;
		border-radius: 14px;
		padding: 6px;
		background-color: #3A3A3A;
		color: #F2F2F7;
		font: 14pt Times New Roman;
		outline: none;
}
	QListWidget::item{
		border-radius: 7px;
		padding: 3px 6px;
}
	QListWidget::item:selected{
		background: #2E5C91;
		color: #FFFFFF;
}
	QLabel{
		color: #F2F2F7;
}
'''


# 样式书的统一做法，要在建任何窗口之前登记：
glass_kit.install_glass_button_class(WhiteButton)   # 白色胶囊 = 玻璃胶囊（5.1）
install_glass_dialog_class(CustomMessageBox)        # 对话框 = 窗口玻璃、圆角 16、系统阴影（5.7）
for _glass_window_cls in (WindowAbout, WindowUpdate, window4, CustomDialog, CustomDialog2, CustomDialog3, CustomDialog4):
	install_native_glass_window_class(_glass_window_cls)   # 系统红绿灯 + 窗口玻璃（5.7.2）
watermelon_ui.set_dialog_host(lambda: globals().get('w3'))
for _all_spaces_cls in (window3, WindowAbout, WindowUpdate, window4, CustomDialog, CustomDialog2, CustomDialog3,
						CustomDialog4, CustomMessageBox, NotesFolderDialog, BusyCard):
	install_all_spaces_class(_all_spaces_cls)   # 每个窗口：在所有桌面显示（开关在菜单栏图标的菜单里）


def _tell_data_folder_moved():
	"""搬完数据的那一次启动提醒一次：数据现在在哪（盯着旧文件夹的同步 / 备份工具要改指向新的）。"""
	watermelon_alert(None, NAME, _tr(
		'Watermelon\'s data has moved from the home folder to:\n\n%1\n\nNothing else changed. If a syncing or backup tool watched the old folder "WatermelonAppPath", point it at the new one.'
	).replace('%1', WATERMELON_DATA_DIR.replace(str(Path.home()), '~', 1)))


if __name__ == '__main__':
	# Apply theme (dark/light mode)
	if is_dark_theme(app):
		app.setStyleSheet(style_sheet_dark)
	else:
		app.setStyleSheet(style_sheet_ori)

	w1 = WindowAbout()
	w2 = WindowUpdate()
	w3 = window3()  # Main window
	w3.setAutoFillBackground(True)
	_apply_window_palette(w3, is_dark_theme(app))
	w4 = window4()
	action1.triggered.connect(w3.addb)
	action2.triggered.connect(w3.pin_a_tab)
	action3.triggered.connect(w1.activate)
	action4.triggered.connect(w3.remb)
	action5.triggered.connect(w2.activate)
	action6.triggered.connect(w4.activate)
	action7.triggered.connect(w3.open_file_menu)
	btna4.triggered.connect(w3.pin_a_tab)
	teleprompter_action.triggered.connect(w3.toggle_teleprompter)
	anki_action.triggered.connect(lambda _checked=False: w3.make_anki_cards())
	lecture_action.triggered.connect(lambda _checked=False: w3.toggle_lecture_mode())
	open_backup_folder_action.triggered.connect(w3.open_current_backup_folder)
	w3.btn0_1.clicked.connect(w4.activate)
	w3.btn0_2.clicked.connect(w3.toggle_notes_mode)
	w3.set_textedit_font(w3._current_font_size, w3._current_font_family)
	apply_bg_color_from_pref(w3)
	# 更新（照 Broccoli，Ryan 2026-11-25：“所有的软件……都是要学习 Broccoli 的这个更新写法的”）：删掉上次更新留下的旧版本 /
	# 安装包；启动 3 秒后在后台查一次 GitHub，有新版本（或上次安装留了话）更新窗口自己出来，里面一键 Update Now。
	# 没有“每 24 小时自动检查”“同一版本不再提醒”这类开关，也没有“打开发布页？”的提问（旧写法，从 Raspberry 继承来的，已删）。
	threading.Thread(target=watermelon_cleanup_update_leftovers, daemon=True,
					 name='watermelon-update-cleanup').start()
	QTimer.singleShot(3000, lambda: w2.checkupdate(popup_when_ready=True))
	# Dock 图标：主窗口建好、“所有桌面”的标记打完以后才放出来。标记要在还没有图标时打上才进得了别的 app 的
	# 全屏桌面（2026-11-19 在 macOS 27 上实测的规律），所以顺序不能反。
	show_window_on_all_spaces(w3)   # 主窗口这时已经显示；别的窗口在各自显示时打（提前建它们的系统窗口会让红绿灯窗口多出一条标题栏的高度）
	set_dock_icon_visible(action_dock_icon.isChecked())
	# Watermelon's functions as tools for AI apps (watermelon_tools.py): a small service on this Mac only, started
	# once the window is up; its card is taken back at quit.
	app_tools = watermelon_tools.WatermelonTools(w3, globals())
	QTimer.singleShot(2000, app_tools.start)
	app.aboutToQuit.connect(app_tools.stop)
	app.aboutToQuit.connect(w3._flush_office_before_quit)
	app.aboutToQuit.connect(w3._lecture_stop_before_quit)   # 退出前撤掉对 Broccoli 语音转写的订阅
	app.aboutToQuit.connect(w3._notes_flush_before_quit)   # 退出前把备忘录里没存的修改存进去   # 退出前把 Office 文件最后的改动存进去
	if DATA_FOLDER_MOVE_REPORT == 'moved':
		QTimer.singleShot(1500, lambda: _tell_data_folder_moved())
	app.exec()
	# 一键更新：等 Qt 收尾之后才替换新旧版本（只有更新窗口在退出前准备好了安装才会执行）
	watermelon_apply_pending_update_install()
