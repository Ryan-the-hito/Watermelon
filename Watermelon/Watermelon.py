#!/usr/local/bin/python3.11
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import base64
import codecs
import hashlib
import json
import html as html_lib
import tempfile
import traceback
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout,
							 QSystemTrayIcon, QMenu, QComboBox,
							 QMenuBar, QFileDialog, QLineEdit,
							 QSplitter, QTextEdit, QListWidget, QCheckBox, QSlider,
							 QFrame, QGraphicsDropShadowEffect, QDialog, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QThread, pyqtSignal, QSize, QEvent, QRectF, QEventLoop, pyqtSlot, QParallelAnimationGroup, QSequentialAnimationGroup, QEasingCurve
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QColor, QFontDatabase, QPixmap, QCursor, QGuiApplication, QPainter, QPen, QPainterPath, QPalette, QFont, QSurfaceFormat, QBrush, QLinearGradient, QImage, QMouseEvent
import PyQt6.QtGui
from PyQt6.QtWebEngineWidgets import QWebEngineView
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

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Watermelon.app/Contents/Resources/'
#BasePath = ''

VERSION = "2.2.3"
NAME = 'Watermelon'

os.environ["QT_QUICK_BACKEND"] = "metal"

fmt = QSurfaceFormat()
fmt.setSamples(8)  # 打开 MSAA 多重采样抗锯齿
QSurfaceFormat.setDefaultFormat(fmt)

NOTES_CACHE_PATH = os.path.join(BasePath, "notes_cache.json")
DEBUG_LAYOUT = False

MODE_BACKUP_LIMIT_MIN = 10
MODE_BACKUP_LIMIT_MAX = 20
DEFAULT_MODE_BACKUP_LIMIT = 20
DEFAULT_AUTO_UPDATE_CHECK_ENABLED = True
DEFAULT_UPDATE_ALERT_DEDUPE_ENABLED = True


def _watermelon_app_path():
	app_path = os.path.join(str(Path.home()), "WatermelonAppPath")
	os.makedirs(app_path, exist_ok=True)
	return app_path


MODE_BACKUP_LIMIT_FILE = os.path.join(_watermelon_app_path(), "backup_limit.txt")
AUTO_UPDATE_CHECK_FILE = os.path.join(_watermelon_app_path(), "auto_update_check.txt")
UPDATE_ALERT_DEDUPE_FILE = os.path.join(_watermelon_app_path(), "update_alert_dedupe.txt")


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


def save_auto_update_check_enabled(enabled):
	value = '1' if bool(enabled) else '0'
	try:
		with open(AUTO_UPDATE_CHECK_FILE, 'w', encoding='utf-8') as f0:
			f0.write(value)
	except Exception:
		pass
	return bool(enabled)


def load_auto_update_check_enabled():
	default_value = DEFAULT_AUTO_UPDATE_CHECK_ENABLED
	try:
		if not os.path.exists(AUTO_UPDATE_CHECK_FILE):
			save_auto_update_check_enabled(default_value)
			return default_value
		raw = codecs.open(AUTO_UPDATE_CHECK_FILE, 'r', encoding='utf-8').read().strip()
		if raw in ('1', 'true', 'True', 'on', 'ON'):
			return True
		if raw in ('0', 'false', 'False', 'off', 'OFF'):
			return False
		save_auto_update_check_enabled(default_value)
		return default_value
	except Exception:
		return default_value


def save_update_alert_dedupe_enabled(enabled):
	value = '1' if bool(enabled) else '0'
	try:
		with open(UPDATE_ALERT_DEDUPE_FILE, 'w', encoding='utf-8') as f0:
			f0.write(value)
	except Exception:
		pass
	return bool(enabled)


def load_update_alert_dedupe_enabled():
	default_value = DEFAULT_UPDATE_ALERT_DEDUPE_ENABLED
	try:
		if not os.path.exists(UPDATE_ALERT_DEDUPE_FILE):
			save_update_alert_dedupe_enabled(default_value)
			return default_value
		raw = codecs.open(UPDATE_ALERT_DEDUPE_FILE, 'r', encoding='utf-8').read().strip()
		if raw in ('1', 'true', 'True', 'on', 'ON'):
			return True
		if raw in ('0', 'false', 'False', 'off', 'OFF'):
			return False
		save_update_alert_dedupe_enabled(default_value)
		return default_value
	except Exception:
		return default_value


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


def _set_auto_update_check_from_menu(checked):
	enabled = save_auto_update_check_enabled(checked)
	if 'auto_update_check_action' in globals():
		try:
			auto_update_check_action.blockSignals(True)
			auto_update_check_action.setChecked(enabled)
			auto_update_check_action.blockSignals(False)
		except Exception:
			pass
	target = globals().get("w3")
	if target is not None:
		try:
			target.set_auto_update_check_enabled(enabled)
		except Exception:
			pass


def _set_update_alert_dedupe_from_menu(checked):
	enabled = save_update_alert_dedupe_enabled(checked)
	if 'update_alert_dedupe_action' in globals():
		try:
			update_alert_dedupe_action.blockSignals(True)
			update_alert_dedupe_action.setChecked(enabled)
			update_alert_dedupe_action.blockSignals(False)
		except Exception:
			pass
	target = globals().get("w3")
	if target is not None:
		try:
			target.set_update_alert_dedupe_enabled(enabled)
		except Exception:
			pass

# Create the icon
icon = QIcon(BasePath + "wtmenu.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()
action1 = QAction("🦾 Bold Text! (Clipboard)")
menu.addAction(action1)

action4 = QAction("💪 Unbold Text! (Clipboard)")
menu.addAction(action4)

menu.addSeparator()

action7 = QAction("📂️ Open a Markdown file")
menu.addAction(action7)

menu.addSeparator()

action2 = QAction("✍️ Watermelon Typewriter")
menu.addAction(action2)
action8 = QAction("🖥️ Assign to All Desktops")
menu.addAction(action8)

action6 = QAction("⚙️ Settings")
menu.addAction(action6)

backup_limit_menu = menu.addMenu("💾 Backup Limit")
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

teleprompter_action = QAction("📺 Teleprompter Mode")
teleprompter_action.setCheckable(True)
menu.addAction(teleprompter_action)
open_backup_folder_action = QAction("🗂️ Open Current Backup Folder")
menu.addAction(open_backup_folder_action)

menu.addSeparator()

action5 = QAction("🆕 Check for Updates")
menu.addAction(action5)

auto_update_check_action = QAction("🔄 Auto Check Updates (24h)")
auto_update_check_action.setCheckable(True)
auto_update_check_action.setChecked(load_auto_update_check_enabled())
auto_update_check_action.triggered.connect(_set_auto_update_check_from_menu)
menu.addAction(auto_update_check_action)

update_alert_dedupe_action = QAction("⏺️ No Alert for the Same Update")
update_alert_dedupe_action.setCheckable(True)
update_alert_dedupe_action.setChecked(load_update_alert_dedupe_enabled())
update_alert_dedupe_action.triggered.connect(_set_update_alert_dedupe_from_menu)
menu.addAction(update_alert_dedupe_action)

action3 = QAction("ℹ️ About")
menu.addAction(action3)

menu.addSeparator()

# Add a Quit option to the menu.
quit = QAction("Quit")
quit.triggered.connect(app.quit)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

# create a system menu
btna4 = QAction("&Watermelon Typewriter")
btna4.setCheckable(True)
sysmenu = QMenuBar()
file_menu = sysmenu.addMenu("&Actions")
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
	bg_pref_file = BasePath + 'bg_color.txt'
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


class UpdateCheckWorker(QThread):
	update_available = pyqtSignal(str)  # latest version, e.g., 'v0.0.13'
	checked_ok = pyqtSignal(str)		# latest version (even if not newer),用于日志或状态
	checked_error = pyqtSignal(str)	 # error message

	def __init__(self, current_version: str, interval_seconds: int = 86400, parent=None):
		super().__init__(parent)
		self._running = True
		self.current_version = current_version  # e.g., 'v0.0.12'
		self.interval_seconds = interval_seconds

	def stop(self):
		self._running = False

	def run(self):
		# 循环：只要应用在运行，就每隔 interval 检查一次
		while self._running:
			try:
				text = WindowUpdate.fetch_latest_version_text()
				latest = WindowUpdate.extract_latest_tag(text) if text else None
				if latest:
					self.checked_ok.emit(latest)
					if is_newer_version(latest, 'v' + VERSION):
						# 通知主线程有新版本
						self.update_available.emit(latest)
				else:
					self.checked_error.emit("No version tag found")
			except Exception as e:
				self.checked_error.emit(str(e))

			# 可中断的“休眠”24小时
			for _ in range(self.interval_seconds):
				if not self._running:
					return
				self.msleep(1000)


def is_macos_16_or_higher():
	"""检测是否为 macOS 16 或更高版本"""
	import platform
	if platform.system() != 'Darwin':
		return False
	try:
		version = platform.mac_ver()[0]
		major = int(version.split('.')[0])
		return major >= 16
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
	singleClicked = pyqtSignal(str)
	rightClicked = pyqtSignal(str)

	def __init__(self, text="Glass Button", radius=30, bg_color=(255, 255, 255, 20), shadow_color=(0, 0, 0, 80), highlight_color=(255, 255, 255, 80), icon_path=None, momentary=False, parent=None):
		super().__init__(text, parent)
		self.radius = radius
		self.momentary = momentary  # True: 按下变灰松开恢复, False: toggle模式
		self.bg_color = QColor(*bg_color)
		self.default_bg_color = QColor(*bg_color)
		self.deep_bg_color = QColor(
			max(0, self.bg_color.red() - 40),
			max(0, self.bg_color.green() - 40),
			max(0, self.bg_color.blue() - 40),
			min(255, self.bg_color.alpha() + 60)
		)
		# hover 时变灰的颜色
		self.hover_bg_color = QColor(
			max(0, self.bg_color.red() - 20),
			max(0, self.bg_color.green() - 20),
			max(0, self.bg_color.blue() - 20),
			min(255, self.bg_color.alpha() + 30)
		)
		self.shadow_color = QColor(*shadow_color)
		self.highlight_color = QColor(*highlight_color)
		self._icon_pixmap = None
		if icon_path:
			self.setIconPath(icon_path)
		self.setStyleSheet("""
			background-color: transparent;
			border: none;
			color: white;
			font-size: 16px;
			padding: 8px 24px;
		""")
		if not is_macos_16_or_higher():
			self.outer_shadow = QGraphicsDropShadowEffect(self)
			self.outer_shadow.setBlurRadius(12)
			self.outer_shadow.setColor(self.shadow_color)
			self.outer_shadow.setOffset(0, 6)
			self.setGraphicsEffect(self.outer_shadow)
		self.pressed_state = False
		self.blur_bg = None
		self.is_selected = False
		self.is_hovered = False

	def setIconPath(self, path):
		"""设置图标路径"""
		if path:
			self._icon_pixmap = QPixmap(path)
		else:
			self._icon_pixmap = None
		self.update()

	def setRadius(self, radius):
		self.radius = radius
		self.update()

	def enterEvent(self, event):
		self.is_hovered = True
		self.update()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.is_hovered = False
		self.update()
		super().leaveEvent(event)

	def isInRoundRect(self, pos):
		rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)
		return path.contains(pos)

	def mousePressEvent(self, event: QMouseEvent):
		if self.isInRoundRect(event.position()):
			if event.button() == Qt.MouseButton.LeftButton:
				if self.momentary:
					# momentary 模式：按下时变灰
					self.pressed_state = True
					self.update()
				else:
					# toggle 模式：原有逻辑
					if self.text() == "Clear" or self.text() == "Tag!" or self.text() == "Close":
						self.singleClicked.emit(self.text())
					elif not self.is_selected:
						self.setSelected(True)
						self.singleClicked.emit(self.text())
			elif event.button() == Qt.MouseButton.RightButton:
				if not self.momentary and self.is_selected:
					self.setSelected(False)
					self.rightClicked.emit(self.text())
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event: QMouseEvent):
		if self.isInRoundRect(event.position()):
			if event.button() == Qt.MouseButton.LeftButton:
				if self.momentary:
					# momentary 模式：松开时恢复
					self.pressed_state = False
					self.update()
				else:
					# toggle 模式：原有逻辑
					self.pressed_state = False
					if self.text() in ("Clear", "Tag!", "Close"):
						self.setSelected(False)
					self.update()
		super().mouseReleaseEvent(event)

	def setSelected(self, selected: bool):
		self.is_selected = selected
		self.update()

	def _getCurrentBgColor(self):
		"""根据当前状态获取背景颜色"""
		if self.pressed_state or self.is_selected:
			return self.deep_bg_color
		elif self.is_hovered:
			return self.hover_bg_color
		else:
			return self.default_bg_color

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
		rect = QRectF(0, 0, self.width(), self.height()).adjusted(2, 2, -2, -2)
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)
		center_y = rect.center().y()

		current_bg = self._getCurrentBgColor()
		painter.setBrush(QBrush(current_bg))
		painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
		painter.drawPath(path)
		if not is_macos_16_or_higher():
			if self.blur_bg is None or self.blur_bg.size() != self.size():
				tmp_img = QImage(self.size(), QImage.Format.Format_ARGB32)
				tmp_img.fill(Qt.GlobalColor.transparent)
				tmp_painter = QPainter(tmp_img)
				tmp_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
				tmp_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
				tmp_painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
				tmp_painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
				tmp_painter.drawPath(path)
				tmp_painter.end()
				pil_img = Image.fromqimage(tmp_img)
				pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=2))
				self.blur_bg = QImage(
					pil_img.tobytes("raw", "RGBA"),
					pil_img.width,
					pil_img.height,
					QImage.Format.Format_ARGB32
				)
			painter.drawImage(0, 0, self.blur_bg)

		if not self.pressed_state:
			path = QPainterPath()
			path.moveTo(rect.left()+self.radius, rect.bottom())
			path.lineTo(rect.right()-self.radius, rect.bottom())
			path.arcTo(rect.right() - 2 * self.radius, rect.bottom() - 2 * self.radius,
					   2 * self.radius, 2 * self.radius, 270, 90)
			path.lineTo(rect.right(), center_y)
			path.lineTo(rect.left(), center_y)
			path.arcTo(rect.left(), rect.bottom() - 2 * self.radius,
					   2 * self.radius, 2 * self.radius, 180, 90)
			path.closeSubpath()
			gradient = QLinearGradient(rect.left(), rect.bottom(),
									   rect.left(), center_y)
			gradient.setColorAt(0, self.highlight_color)
			gradient.setColorAt(1, QColor(255, 255, 255, 0))
			painter.setPen(QPen(QBrush(gradient), 2))
			painter.setBrush(Qt.BrushStyle.NoBrush)
			painter.drawPath(path)

		# 绘制图标或文字
		if self._icon_pixmap and not self._icon_pixmap.isNull():
			# 绘制图标，居中显示
			icon_size = min(rect.width(), rect.height()) * 0.6
			scaled_pixmap = self._icon_pixmap.scaled(
				int(icon_size), int(icon_size),
				Qt.AspectRatioMode.KeepAspectRatio,
				Qt.TransformationMode.SmoothTransformation
			)
			icon_x = rect.center().x() - scaled_pixmap.width() / 2
			icon_y = rect.center().y() - scaled_pixmap.height() / 2
			painter.drawPixmap(int(icon_x), int(icon_y), scaled_pixmap)
		else:
			painter.setPen(QPen(QColor(255, 255, 255, 255)))
			painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class WhiteButton(QPushButton):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)
		self.setFixedHeight(30)
		self.setStyleSheet("""
		QPushButton {
			background-color: white;
			color: #444;
			border: none;
			border-radius: 15px;
			font-size: 13px;
			padding: 5px 20px;
		}
		QPushButton:hover {
			background-color: #f5f5f5;
		}
		""")

		shadow = QGraphicsDropShadowEffect(self)
		shadow.setBlurRadius(40)
		shadow.setXOffset(0)
		shadow.setYOffset(0)
		shadow.setColor(QColor(0, 0, 0, 40))  # 半透明黑色阴影
		self.setGraphicsEffect(shadow)


class MacNormalButton(QPushButton):
	def __init__(self, text, parent=None, always_dark=False):
		super().__init__(text, parent)
		self.setAutoDefault(False)
		self.setFixedHeight(22)
		self._always_dark = bool(always_dark)
		self._alert = False
		self._updating_style = False
		self.update_theme()

	def update_theme(self):
		if self._updating_style:
			return
		self._updating_style = True
		try:
			if self._alert:
				bg = "#FF4D4D"
				bg_hover = "#FF6666"
				bg_pressed = "#CC3D3D"
				bg_disabled = "#E6E6E6"
				text = "#FFFFFF"
				text_disabled = "#777777"
			else:
				dark = self._always_dark or is_dark_theme(app)
				if dark:
					bg = "#404145"
					bg_hover = "#4A4B4F"
					bg_pressed = "#343538"
					bg_disabled = "#2F3033"
					text = "#FFFFFF"
					text_disabled = "#777777"
				else:
					bg = "#E7E7E7"
					bg_hover = "#EEEEEE"
					bg_pressed = "#DCDCDC"
					bg_disabled = "#E1E1E1"
					text = "#111111"
					text_disabled = "#777777"
			self.setStyleSheet(f"""
				QPushButton {{
					border: 1px solid transparent;
					background-color: {bg};
					border-radius: 6px;
					padding: 1px 8px;
					color: {text};
				}}
				QPushButton:hover {{
					background-color: {bg_hover};
				}}
				QPushButton:pressed {{
					background-color: {bg_pressed};
				}}
				QPushButton:disabled {{
					background-color: {bg_disabled};
					color: {text_disabled};
				}}
			""")
		finally:
			self._updating_style = False

	def changeEvent(self, event):
		super().changeEvent(event)
		if self._updating_style:
			return
		if event.type() in (
			QEvent.Type.PaletteChange,
			QEvent.Type.ApplicationPaletteChange,
		):
			self.update_theme()

	def set_alert(self, enabled):
		enabled = bool(enabled)
		if self._alert == enabled:
			return
		self._alert = enabled
		self.update_theme()


class DropdownPopup(QWidget):
	"""暗色主题的弹出列表窗口，带圆角、hover效果，失去焦点自动关闭"""
	item_selected = pyqtSignal(int)  # 选中项目时发出信号，传递索引

	def __init__(self, parent_button):
		super().__init__(None)
		self.parent_button = parent_button
		self.items = []
		self.current_index = -1
		self.hovered_index = -1
		self.item_height = 28
		self.padding = 6

		# 设置窗口属性 - 使用 Popup 类型确保点击外部自动关闭
		self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setMouseTracking(True)

	def set_items(self, items):
		"""设置列表项"""
		self.items = list(items)
		self._update_size()

	def set_current_index(self, index):
		"""设置当前选中项"""
		if 0 <= index < len(self.items):
			self.current_index = index
		else:
			self.current_index = -1
		self.update()

	def _update_size(self):
		"""根据内容更新窗口大小"""
		if not self.items:
			return
		# 计算所需宽度（至少与父按钮一样宽）
		fm = self.fontMetrics()
		max_width = self.parent_button.width()
		for item in self.items:
			text_width = fm.horizontalAdvance(item) + 24
			max_width = max(max_width, text_width)

		height = len(self.items) * self.item_height + self.padding * 2
		max_height = 400  # 最大高度限制
		if height > max_height:
			height = max_height
		self.setFixedSize(max_width, height)

	def show_above_button(self):
		"""在父按钮上方显示弹出窗口"""
		if not self.items:
			return
		self._update_size()
		# 获取按钮的全局位置，在上方显示
		btn_pos = self.parent_button.mapToGlobal(self.parent_button.rect().topLeft())
		# 弹出窗口显示在按钮上方，需要减去弹出窗口的高度
		self.move(btn_pos.x(), btn_pos.y() - self.height() - 2)
		self.show()
		self.activateWindow()  # 确保窗口被激活

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)

		# 绘制背景（带圆角和半透明效果）
		bg_path = QPainterPath()
		bg_path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
		painter.fillPath(bg_path, QColor(45, 45, 48, 245))

		# 绘制边框
		painter.setPen(QPen(QColor(70, 70, 75), 1))
		painter.drawPath(bg_path)

		# 绘制列表项
		y = self.padding
		for i, item in enumerate(self.items):
			item_rect = QRectF(self.padding, y, self.width() - self.padding * 2, self.item_height)

			# 绘制hover/选中背景
			if i == self.hovered_index:
				hover_path = QPainterPath()
				hover_path.addRoundedRect(item_rect, 4, 4)
				painter.fillPath(hover_path, QColor(80, 80, 85))
			elif i == self.current_index:
				select_path = QPainterPath()
				select_path.addRoundedRect(item_rect, 4, 4)
				painter.fillPath(select_path, QColor(0, 122, 255, 100))

			# 绘制文本
			painter.setPen(QColor(240, 240, 240))
			text_rect = item_rect.adjusted(8, 0, -8, 0)
			painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, item)

			y += self.item_height
			if y > self.height() - self.padding:
				break

	def mouseMoveEvent(self, event):
		# 计算鼠标所在的项目索引
		y = event.position().y() - self.padding
		index = int(y // self.item_height)
		if 0 <= index < len(self.items):
			if self.hovered_index != index:
				self.hovered_index = index
				self.update()
		else:
			if self.hovered_index != -1:
				self.hovered_index = -1
				self.update()

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			y = event.position().y() - self.padding
			index = int(y // self.item_height)
			if 0 <= index < len(self.items):
				self.current_index = index
				self.item_selected.emit(index)
				self.hide()

	def leaveEvent(self, event):
		self.hovered_index = -1
		self.update()

	def focusOutEvent(self, event):
		self.hide()


class DropdownButton(QPushButton):
	"""自定义下拉按钮，点击显示弹出列表"""
	currentIndexChanged = pyqtSignal(int)  # 兼容 QComboBox 的信号

	def __init__(self, parent=None, always_dark=True):
		super().__init__(parent)
		self.setAutoDefault(False)
		self._items = []
		self._item_data = []  # 存储每个项目的附加数据
		self._current_index = -1
		self._always_dark = always_dark
		self._enabled = True
		self._signals_blocked = False

		# 创建弹出窗口
		self._popup = DropdownPopup(self)
		self._popup.item_selected.connect(self._on_item_selected)

		self.clicked.connect(self._show_popup)
		self._update_style()

	def _update_style(self):
		"""更新按钮样式"""
		if self._enabled:
			bg = "#404145"
			bg_hover = "#4A4B4F"
			bg_pressed = "#343538"
			text = "#FFFFFF"
		else:
			bg = "#2F3033"
			bg_hover = "#2F3033"
			bg_pressed = "#2F3033"
			text = "#777777"

		self.setStyleSheet(f"""
			QPushButton {{
				border: 1px solid transparent;
				background-color: {bg};
				border-radius: 6px;
				padding: 1px 8px;
				color: {text};
				text-align: left;
			}}
			QPushButton:hover {{
				background-color: {bg_hover};
			}}
			QPushButton:pressed {{
				background-color: {bg_pressed};
			}}
			QPushButton::menu-indicator {{
				width: 0px;
			}}
		""")

	def _show_popup(self):
		"""显示或隐藏弹出窗口"""
		if not self._enabled or not self._items:
			return
		# 如果弹出窗口已显示，则关闭它
		if self._popup.isVisible():
			self._popup.hide()
			return
		self._popup.set_items(self._items)
		self._popup.set_current_index(self._current_index)
		self._popup.show_above_button()

	def _on_item_selected(self, index):
		"""处理弹出窗口中的项目选择"""
		if index != self._current_index:
			self._current_index = index
			self._update_text()
			if not self._signals_blocked:
				self.currentIndexChanged.emit(index)

	def _update_text(self):
		"""更新按钮显示的文本"""
		if 0 <= self._current_index < len(self._items):
			text = self._items[self._current_index]
			# 如果文本太长，截断并添加省略号
			fm = self.fontMetrics()
			available_width = self.width() - 20
			if fm.horizontalAdvance(text) > available_width:
				while fm.horizontalAdvance(text + "...") > available_width and len(text) > 0:
					text = text[:-1]
				text += "..."
			self.setText(text)
		else:
			self.setText("")

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._update_text()

	# 兼容 QComboBox 的 API
	def addItem(self, text, data=None):
		"""添加单个项目"""
		self._items.append(text)
		self._item_data.append(data)
		if self._current_index == -1:
			self.setCurrentIndex(0)

	def addItems(self, texts):
		"""添加多个项目"""
		for text in texts:
			self._items.append(text)
			self._item_data.append(None)
		if self._current_index == -1 and self._items:
			self.setCurrentIndex(0)

	def clear(self):
		"""清空所有项目"""
		self._items = []
		self._item_data = []
		self._current_index = -1
		self.setText("")

	def count(self):
		"""返回项目数量"""
		return len(self._items)

	def currentIndex(self):
		"""返回当前选中的索引"""
		return self._current_index

	def setCurrentIndex(self, index):
		"""设置当前选中的索引"""
		if 0 <= index < len(self._items):
			old_index = self._current_index
			self._current_index = index
			self._update_text()
			if old_index != index and not self._signals_blocked:
				self.currentIndexChanged.emit(index)
		elif index == -1 or not self._items:
			self._current_index = -1
			self.setText("")

	def currentText(self):
		"""返回当前选中项的文本"""
		if 0 <= self._current_index < len(self._items):
			return self._items[self._current_index]
		return ""

	def itemText(self, index):
		"""返回指定索引的文本"""
		if 0 <= index < len(self._items):
			return self._items[index]
		return ""

	def itemData(self, index):
		"""返回指定索引的附加数据"""
		if 0 <= index < len(self._item_data):
			return self._item_data[index]
		return None

	def setItemData(self, index, data):
		"""设置指定索引的附加数据"""
		if 0 <= index < len(self._item_data):
			self._item_data[index] = data

	def setEnabled(self, enabled):
		"""设置是否启用"""
		self._enabled = enabled
		super().setEnabled(enabled)
		self._update_style()

	def blockSignals(self, block):
		"""阻止信号发射"""
		self._signals_blocked = block
		return super().blockSignals(block)


class MacWindowButton(QPushButton):
	def __init__(self, color, symbol, parent=None):
		super().__init__(parent)
		self.setFixedSize(16,16)
		self.base_color = QColor(color)
		self.symbol = symbol  # "x", "-", "+"
		self.hovered = False
		self.setStyleSheet("border: none; background: transparent;")

	def enterEvent(self, event):
		self.hovered = True
		self.update()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.hovered = False
		self.update()
		super().leaveEvent(event)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
		# # 1. 选择底色
		# if self.hovered:
		#	 # hover 时用更深的颜色
		#	 if self.symbol == "x":
		#		 color = QColor("#BF4943")
		#	 elif self.symbol == "-":
		#		 color = QColor("#B29B32")
		#	 elif self.symbol == "+":
		#		 color = QColor("#24912D")
		#	 else:
		#		 color = self.base_color
		# else:
		#	 color = self.base_color
		# Draw circle
		painter.setBrush(self.base_color)
		painter.setPen(Qt.PenStyle.NoPen)
		painter.drawEllipse(0, 0, self.width(), self.height())
		# Draw symbol if hovered
		if self.hovered:
			pen = QPen(QColor("black"))
			pen.setWidth(2)
			painter.setPen(pen)
			margin = 5  # 增大 margin，叉号更小
			if self.symbol == "x":
				painter.drawLine(margin, margin, self.width()-margin, self.height()-margin)
				painter.drawLine(self.width()-margin, margin, margin, self.height()-margin)
			elif self.symbol == "-":
				painter.drawLine(margin, self.height()//2, self.width()-margin, self.height()//2)
			elif self.symbol == "+":
				painter.drawLine(self.width()//2, margin, self.width()//2, self.height()-margin)
				painter.drawLine(margin, self.height()//2, self.width()-margin, self.height()//2)


class CustomMessageBox(QWidget):
	def __init__(
		self,
		text=None,
		parent=None,
		icon=None,
		buttons=("OK",),
		default=0,
		fixed_size=(400, 200),
		show_close_button=True,
	):
		super().__init__(parent)
		self.radius = 16
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
		if fixed_size:
			self.setFixedSize(fixed_size[0], fixed_size[1])
		self.result = None
		self._dialog_result = None
		self._event_loop = None

		# 拖动支持
		self.drag_pos = None

		# 关闭按钮
		self.close_button = None
		if show_close_button:
			self.close_button = MacWindowButton("#FF605C", "x", self)
			self.close_button.move(10, 10)
			self.close_button.clicked.connect(self.reject)

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
			label.setStyleSheet("""
				font-size: 16px;
				background-color: rgba(255,255,255,0);
				border-radius: 8px;
				padding: 8px;
			""")
			self.body_layout.addWidget(label, stretch=1)
			self.label = label

		# 按钮
		self.btns = []
		if buttons:
			btn_layout = QHBoxLayout()
			btn_layout.addStretch()
			for i, btn_text in enumerate(buttons):
				btn = WhiteButton(btn_text)
				btn.setFixedWidth(150)
				btn.clicked.connect(lambda checked, idx=i: self._on_btn(idx))
				btn_layout.addWidget(btn)
				self.btns.append(btn)
			btn_layout.addStretch()
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

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		rect = QRectF(self.rect())
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)
		painter.setClipPath(path)
		if is_dark_theme(self):
			painter.fillPath(path, QColor(30, 30, 30, 245))
		else:
			painter.fillPath(path, QColor(255, 255, 255, 245))

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
		self.radius = 16  # 圆角半径，可按 macOS 15 或 26 设置为 16~26

		self.setWindowFlags(
			Qt.WindowType.FramelessWindowHint |
			Qt.WindowType.Window |
			Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

		self.init_ui()

	def init_ui(self):
		self.setUpMainWindow()
		self.setFixedSize(400, 600)
		self.center()
		self.setFocus()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

		rect = QRectF(self.rect())
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)

		painter.setClipPath(path)
		bg_color = self.palette().color(QPalette.ColorRole.Window)
		painter.fillPath(path, bg_color)

	# 让无边框窗口可拖动
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.drag_pos)
			event.accept()

	def setUpMainWindow(self):
		# 添加关闭按钮（仿 macOS 左上角红色圆点）
		# self.close_button = QPushButton(self)
		# self.close_button.setFixedSize(12, 12)
		# self.close_button.move(10, 10)
		# self.close_button.setStyleSheet("""
		#	 QPushButton {
		#		 background-color: #FF5F57;
		#		 border-radius: 6px;
		#		 border: none;
		#	 }
		#	 QPushButton:hover {
		#		 background-color: #BF4943;
		#	 }
		# """)
		# self.close_button.clicked.connect(self.close)
		# 三个按钮
		##FF5F57
		self.close_button = MacWindowButton("#FF605C", "x", self)
		self.close_button.move(10, 10)
		self.close_button.clicked.connect(self.close)
		##FFBD2E
		# self.min_button = MacWindowButton("#FFBD44", "-", self)
		# self.min_button.move(30, 10)
		# self.min_button.clicked.connect(self.showMinimized)
		##28C940
		# self.max_button = MacWindowButton("#00CA4E", "+", self)
		# self.max_button.move(50, 10)
		# self.max_button.clicked.connect(self.showMaximized)

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
		lbl1 = QLabel(self.tr(f'Version %n').replace('%n', VERSION), self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(lbl1)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		lbl2 = QLabel(self.tr('Thanks for your love🤟.'), self)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		blay4.addStretch()
		blay4.addWidget(lbl2)
		blay4.addStretch()
		widg4.setLayout(blay4)

		widg5 = QWidget()
		lbl3 = QLabel(self.tr('For more of my works, please visit the homepage🥰.'), self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.addStretch()
		blay5.addWidget(lbl3)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg6 = QWidget()
		lbl4 = QLabel(self.tr('Special thanks to ut.code(); of the University of Tokyo❤️.'), self)
		blay6 = QHBoxLayout()
		blay6.setContentsMargins(0, 0, 0, 0)
		blay6.addStretch()
		blay6.addWidget(lbl4)
		blay6.addStretch()
		widg6.setLayout(blay6)

		widg7 = QWidget()
		lbl5 = QLabel(self.tr('This app is under the protection of GPL-3.0 license.'), self)
		blay7 = QHBoxLayout()
		blay7.setContentsMargins(0, 0, 0, 0)
		blay7.addStretch()
		blay7.addWidget(lbl5)
		blay7.addStretch()
		widg7.setLayout(blay7)

		widg8 = QWidget()
		widg8.setFixedHeight(50)
		bt1 = WhiteButton(self.tr('The Author'))
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.intro)
		bt2 = WhiteButton(self.tr('Github Page'))
		bt2.setMinimumWidth(100)
		bt2.clicked.connect(self.homepage)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg8.setLayout(blay8)

		bt7 = WhiteButton(self.tr('Buy me a cup of coffee☕'))
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
		self.setWindowTitle(self.tr("Thank you for your support!"))
		self.center()
		self.resize(440, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

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

		m1 = QLabel(self.tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(self.tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(self.tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(self.tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
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
		self.setWindowTitle(self.tr("Thank you for your support!"))
		self.center()
		self.resize(440, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

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

		m1 = QLabel(self.tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(self.tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(self.tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(self.tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
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
		self.setWindowTitle(self.tr("Thank you for your support!"))
		self.center()
		self.resize(440, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

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

		m1 = QLabel(self.tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(self.tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(self.tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(self.tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
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
		self.setWindowTitle(self.tr("Thank you for your support!"))
		self.center()
		self.resize(440, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

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

		m1 = QLabel(self.tr('Thank you for your kind support! 😊'), self)
		m2 = QLabel(self.tr('I will write more interesting apps! 🥳'), self)

		widg_c = QWidget()
		widg_c.setFixedHeight(50)
		bt1 = WhiteButton(self.tr('Thank you!'))
		#bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = WhiteButton(self.tr('Neither one above? Buy me a coffee~'))
		#bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(260)
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


class WindowUpdate(QWidget):  # 增加更新页面（Check for Updates）
	def __init__(self):
		super().__init__()
		self.radius = 16  # 圆角半径，可按 macOS 15 或 26 设置为 16~26

		self.setWindowFlags(
			Qt.WindowType.FramelessWindowHint |
			Qt.WindowType.Window |
			Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

		self.init_ui()

	def init_ui(self):
		self.setUpMainWindow()
		self.setFixedSize(280, 220)
		self.center()
		self.setFocus()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

		rect = QRectF(self.rect())
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)

		painter.setClipPath(path)
		bg_color = self.palette().color(QPalette.ColorRole.Window)
		painter.fillPath(path, bg_color)

	# 让无边框窗口可拖动
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.drag_pos)
			event.accept()

	def setUpMainWindow(self):
		# 添加关闭按钮（仿 macOS 左上角红色圆点）
		# self.close_button = QPushButton(self)
		# self.close_button.setFixedSize(12, 12)
		# self.close_button.move(10, 10)
		# self.close_button.setStyleSheet("""
		#	 QPushButton {
		#		 background-color: #FF5F57;
		#		 border-radius: 6px;
		#		 border: none;
		#	 }
		#	 QPushButton:hover {
		#		 background-color: #BF4943;
		#	 }
		# """)
		# self.close_button.clicked.connect(self.close)
		self.close_button = MacWindowButton("#FF605C", "x", self)
		self.close_button.move(10, 10)
		self.close_button.clicked.connect(self.close)

		title = QLabel(self.tr("<h2>Watermelon Update</h2>"))
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)

		widg5 = QWidget()
		lbl1 = QLabel(self.tr('Latest version:'), self)
		self.lbl2 = QLabel('', self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		# blay5.addStretch()
		blay5.addWidget(lbl1)
		blay5.addWidget(self.lbl2)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg3 = QWidget()
		self.lbl = QLabel(self.tr(f'Current version: v%n').replace('%n', VERSION), self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		# blay3.addStretch()
		blay3.addWidget(self.lbl)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		widg4.setFixedHeight(50)
		lbl0 = QLabel(self.tr('Check release:'), self)
		bt1 = WhiteButton('Github')
		bt1.clicked.connect(self.upd)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		# blay4.addStretch()
		blay4.addWidget(lbl0)
		blay4.addWidget(bt1)
		blay4.addStretch()
		widg4.setLayout(blay4)

		main_h_box = QVBoxLayout()
		main_h_box.setContentsMargins(20, 40, 20, 20)  # 重要，用来保证关闭按钮的位置。
		main_h_box.addWidget(title)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg5)
		main_h_box.addSpacing(5)
		main_h_box.addWidget(widg3)
		main_h_box.addWidget(widg4)
		self.setLayout(main_h_box)

	def upd(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Watermelon/releases')

	def center(self):  # 设置窗口居中
		qr = self.frameGeometry()
		cp = self.screen().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def activate(self):  # 设置窗口显示
		self.show()
		self.checkupdate()

	def checkupdate(self):
		targetURL = 'https://github.com/Ryan-the-hito/Watermelon/releases'
		try:
			# Fetch the HTML content from the URL
			urllib3.disable_warnings()
			logging.captureWarnings(True)
			s = requests.session()
			s.keep_alive = False  # 关闭多余连接
			response = s.get(targetURL, verify=False)
			response.encoding = 'utf-8'
			html_content = response.text
			# Parse the HTML using BeautifulSoup
			soup = BeautifulSoup(html_content, "html.parser")
			# Remove all images from the parsed HTML
			for img in soup.find_all("img"):
				img.decompose()
			# Convert the parsed HTML to plain text using html2text
			text_maker = html2text.HTML2Text()
			text_maker.ignore_links = True
			text_maker.ignore_images = True
			plain_text = text_maker.handle(str(soup))
			# Convert the plain text to UTF-8
			plain_text_utf8 = plain_text.encode(response.encoding).decode("utf-8")

			for i in range(10):
				plain_text_utf8 = plain_text_utf8.replace('\n\n\n\n', '\n\n')
				plain_text_utf8 = plain_text_utf8.replace('\n\n\n', '\n\n')
				plain_text_utf8 = plain_text_utf8.replace('   ', ' ')
				plain_text_utf8 = plain_text_utf8.replace('  ', ' ')

			pattern2 = re.compile(r'(v\d+\.\d+\.\d+)\sLatest')
			result = pattern2.findall(plain_text_utf8)
			result = ''.join(result)
			nowversion = 'v' + VERSION
			if result == nowversion:
				alertupdate = result + self.tr(' (up-to-date)')
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
			else:
				alertupdate = result + self.tr(' is ready!')
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
		except:
			alertupdate = self.tr('No Intrenet')
			self.lbl2.setText(alertupdate)
			self.lbl2.adjustSize()

	@staticmethod
	def fetch_latest_version_text():
		# 返回页面纯文本，或直接返回最新版本字符串
		targetURL = 'https://github.com/Ryan-the-hito/Watermelon/releases'
		try:
			urllib3.disable_warnings()
			logging.captureWarnings(True)
			s = requests.session()
			s.keep_alive = False
			response = s.get(targetURL, verify=False, timeout=15)
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

MD_EMBED_TAG_ID = "md-source-7c3a6b24"
CACHE_DIR = Path.home() / "Library" / "Caches" / "NotesMarkdown"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MD_EMBED_PREFIX = f'<div id="{MD_EMBED_TAG_ID}" style="display:none;white-space:pre-wrap;">'
MD_EMBED_SUFFIX = '</div>'


def cache_path_for(cache_key):
	safe = re.sub(r"[^A-Za-z0-9._-]+", "_", cache_key).strip("_")
	digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:12]
	name = safe or "note"
	return CACHE_DIR / f"{name}_{digest}.md"


def write_cache_markdown(cache_key, md):
	path = cache_path_for(cache_key)
	path.write_text(md, encoding="utf-8")


def delete_cache_file(cache_key):
	path = cache_path_for(cache_key)
	try:
		path.unlink()
	except FileNotFoundError:
		pass


# def cache_tag_for(cache_key):
# 	return f"[[MD-CACHE:{cache_key}]]"


def read_cache_markdown(cache_key):
	path = cache_path_for(cache_key)
	if not path.exists():
		return None
	try:
		text = path.read_text(encoding="utf-8")
	except OSError:
		return None
	match = re.search(r"MD64:([A-Za-z0-9+/=\\s]+)", text)
	if match:
		b64 = re.sub(r"\\s+", "", match.group(1))
		try:
			return base64.b64decode(b64).decode("utf-8")
		except Exception:
			return None
	return text


def strip_embedded_markdown(html):
	pattern = re.compile(
		r'<div id="' + re.escape(MD_EMBED_TAG_ID) + r'"[^>]*>.*?</div>',
		re.DOTALL | re.IGNORECASE,
	)
	return pattern.sub("", html)


def extract_embedded_markdown(html):
	pattern = re.compile(
		r'<div id="' + re.escape(MD_EMBED_TAG_ID) + r'"[^>]*>(.*?)</div>',
		re.DOTALL | re.IGNORECASE,
	)
	match = pattern.search(html)
	if not match:
		return None
	try:
		b64 = match.group(1).strip()
		b64 = re.sub(r"\\s+", "", b64)
		raw = base64.b64decode(b64)
		return raw.decode("utf-8")
	except Exception:
		return None


def embed_markdown(html, md):
	clean_html = strip_embedded_markdown(html).strip()
	b64 = base64.b64encode(md.encode("utf-8")).decode("ascii")
	return f"{clean_html}{MD_EMBED_PREFIX}{b64}{MD_EMBED_SUFFIX}\n"


# def html_to_plain(html):
# 	converter = html2text.HTML2Text()
# 	converter.body_width = 0
# 	converter.ignore_links = True
# 	converter.ignore_images = True
# 	converter.single_line_break = True
# 	return converter.handle(html)


# def preprocess_notes_html(html):
# 	placeholders = {}
# 	processed_html = fix_list_nesting(html)
#
# 	def create_placeholder_raw(markdown_text):
# 		placeholder = f"@@PH{uuid.uuid4().hex}@@"
# 		placeholders[placeholder] = markdown_text
# 		return f"<div>{placeholder}</div>"
#
# 	def strip_tags(text):
# 		return re.sub(r'<[^>]+>', '', text)
#
# 	def normalize_ws(text):
# 		text = text.replace("&quot", '"')
# 		text = html_lib.unescape(text)
# 		text = text.replace("\u00a0", " ")
# 		return re.sub(r'\s+', ' ', text).strip()
#
# 	def clean_code_line(text):
# 		text = text.replace("&quot", '"')
# 		text = html_lib.unescape(text)
# 		text = text.replace("\u00a0", " ")
# 		return text.rstrip("\n")
#
# 	def extract_span_text(inner, size_px):
# 		spans = re.findall(
# 			rf'<span[^>]*font-size:\s*{size_px}px[^>]*>(.*?)</span>',
# 			inner,
# 			re.IGNORECASE | re.DOTALL,
# 		)
# 		if not spans:
# 			return None
# 		text = normalize_ws(''.join(strip_tags(s) for s in spans))
# 		return text if text else None
#
# 	def replace_font_heading(match, size_px, prefix):
# 		inner = match.group(1)
# 		if not re.search(rf'font-size:\s*{size_px}px', inner, re.IGNORECASE):
# 			return match.group(0)
# 		text = extract_span_text(inner, size_px)
# 		if not text:
# 			return match.group(0)
# 		return create_placeholder_raw(f"\n\n{prefix} {text}\n")
#
# 	def convert_table(table_html):
# 		rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
# 		if not rows:
# 			return None
# 		parsed = []
# 		header_cells_html = None
# 		max_cols = 0
# 		for row_idx, row in enumerate(rows):
# 			cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.IGNORECASE | re.DOTALL)
# 			if not cells:
# 				continue
# 			texts = [normalize_ws(strip_tags(c)) for c in cells]
# 			parsed.append(texts)
# 			max_cols = max(max_cols, len(texts))
# 			if row_idx == 0:
# 				header_cells_html = cells
# 		if not parsed:
# 			return None
# 		for row in parsed:
# 			if len(row) < max_cols:
# 				row.extend([""] * (max_cols - len(row)))
# 		header = parsed[0]
# 		aligns = [":---"] * max_cols
# 		if header_cells_html:
# 			extra_bold = []
# 			for idx, cell_html in enumerate(header_cells_html):
# 				if re.search(r'text-align\s*:\s*center', cell_html, re.IGNORECASE):
# 					aligns[idx] = ":---:"
# 					continue
# 				if re.search(r'text-align\s*:\s*right', cell_html, re.IGNORECASE):
# 					aligns[idx] = "---:"
# 					continue
# 				if len(re.findall(r'<b\b', cell_html, re.IGNORECASE)) > 1:
# 					extra_bold.append(idx)
# 			if extra_bold:
# 				if len(extra_bold) >= 1:
# 					aligns[extra_bold[0]] = ":---:"
# 				if len(extra_bold) >= 2:
# 					aligns[extra_bold[1]] = "---:"
# 		lines = [
# 			"| " + " | ".join(header) + " |",
# 			"| " + " | ".join(aligns) + " |",
# 		]
# 		for row in parsed[1:]:
# 			lines.append("| " + " | ".join(row) + " |")
# 		return "\n".join(lines)
#
# 	pattern_table = re.compile(
# 		r'<object>\s*(<table[^>]*>.*?</table>)\s*</object>',
# 		re.IGNORECASE | re.DOTALL,
# 	)
#
# 	def replace_table(match):
# 		md_table = convert_table(match.group(1))
# 		if not md_table:
# 			return match.group(0)
# 		return create_placeholder_raw(f"\n\n{md_table}\n\n")
#
# 	processed_html = pattern_table.sub(replace_table, processed_html)
#
# 	pattern_div = re.compile(r'<div>(.*?)</div>', re.IGNORECASE | re.DOTALL)
# 	processed_html = pattern_div.sub(lambda m: replace_font_heading(m, 24, "#"), processed_html)
# 	processed_html = pattern_div.sub(lambda m: replace_font_heading(m, 18, "##"), processed_html)
#
# 	pattern_h3 = re.compile(
# 		r'<div>\s*<b>(.*?)</b>\s*<b>\s*\(H3\)\s*</b>\s*</div>',
# 		re.IGNORECASE | re.DOTALL,
# 	)
# 	processed_html = pattern_h3.sub(
# 		lambda m: create_placeholder_raw(
# 			f"\n\n### {normalize_ws(strip_tags(m.group(1)))} (H3)\n"
# 		),
# 		processed_html,
# 	)
#
# 	bold_div_pattern = r'<div>\s*(?:<b>.*?</b>\s*|<br\s*/?>\s*)+</div>'
#
# 	def bold_div_text(div_html):
# 		text = normalize_ws(strip_tags(div_html))
# 		return re.sub(r"\s+([:：,，.!?？！])", r"\1", text)
#
# 	pattern_code_label = re.compile(
# 		bold_div_pattern + r'(?=\s*<div>\s*<font[^>]*face="Courier"[^>]*>\s*<tt>)',
# 		re.IGNORECASE | re.DOTALL,
# 	)
# 	processed_html = pattern_code_label.sub(
# 		lambda m: create_placeholder_raw(f"**{bold_div_text(m.group(0))}**\n"),
# 		processed_html,
# 	)
#
# 	pattern_list_heading = re.compile(
# 		bold_div_pattern + r'(?=\s*<(ul|ol)\b)',
# 		re.IGNORECASE | re.DOTALL,
# 	)
# 	processed_html = pattern_list_heading.sub(
# 		lambda m: create_placeholder_raw(f"\n\n**{bold_div_text(m.group(0))}**\n"),
# 		processed_html,
# 	)
#
# 	pattern_table_heading = re.compile(
# 		bold_div_pattern + r'(?=\s*<div>\s*<object>)',
# 		re.IGNORECASE | re.DOTALL,
# 	)
# 	processed_html = pattern_table_heading.sub(
# 		lambda m: create_placeholder_raw(f"\n\n**{bold_div_text(m.group(0))}**\n"),
# 		processed_html,
# 	)
#
# 	pattern_bold_div = re.compile(
# 		bold_div_pattern
# 		+ r'(?!\s*<(ul|ol)\b)'
# 		+ r'(?!\s*<div>\s*<object)'
# 		+ r'(?!\s*<div>\s*<font[^>]*face="Courier")',
# 		re.IGNORECASE | re.DOTALL,
# 	)
#
# 	def replace_bold_div(match):
# 		inner = match.group(0)
# 		if re.search(r'font-size', inner, re.IGNORECASE):
# 			return inner
# 		text = bold_div_text(inner)
# 		if not text:
# 			return inner
# 		return create_placeholder_raw(f"\n\n**{text}**\n")
#
# 	processed_html = pattern_bold_div.sub(replace_bold_div, processed_html)
#
# 	processed_html = replace_lists_with_markdown(
# 		processed_html,
# 		create_placeholder_raw,
# 		normalize_ws,
# 		strip_tags,
# 	)
#
# 	pattern_code_block = re.compile(
# 		r'(?:<div>\s*<font[^>]*face="Courier"[^>]*>\s*<tt>.*?</tt>\s*</font>\s*</div>\s*){1,}',
# 		re.IGNORECASE | re.DOTALL,
# 	)
#
# 	def replace_code_block(match):
# 		block = match.group(0)
# 		lines = re.findall(r'<tt>(.*?)</tt>', block, re.IGNORECASE | re.DOTALL)
# 		if not lines:
# 			return match.group(0)
# 		cleaned = [clean_code_line(line) for line in lines]
# 		fence = "```\n" + "\n".join(cleaned) + "\n```\n"
# 		return create_placeholder_raw(f"\n\n{fence}\n")
#
# 	processed_html = pattern_code_block.sub(replace_code_block, processed_html)
#
# 	processed_html = rewrite_list_items(processed_html, normalize_ws, strip_tags)
#
# 	return processed_html, placeholders


def strip_tags(text):
	return re.sub(r"<[^>]+>", "", text)


def normalize_ws(text):
	text = text.replace("&quot", '"')
	text = html_lib.unescape(text)
	text = text.replace("\u00a0", " ")
	return re.sub(r"\s+", " ", text).strip()


def inline_html_to_markdown(fragment):
	if not fragment:
		return ""
	soup = BeautifulSoup(fragment, "html.parser")

	def emphasis_kind(tag):
		name = tag.name.lower()
		if name in ("b", "strong"):
			return "bold"
		if name in ("i", "em"):
			return "italic"
		if name in ("s", "strike", "del"):
			return "strike"
		return None

	def is_ws_node(node):
		if not isinstance(node, NavigableString):
			return False
		text = str(node).replace("\u00a0", " ")
		return text.strip() == ""

	def merge_adjacent_emphasis(parent):
		node = parent.contents[0] if parent.contents else None
		while node is not None:
			if isinstance(node, Tag):
				kind = emphasis_kind(node)
				if kind:
					while True:
						nxt = node.next_sibling
						if nxt is None:
							break
						if is_ws_node(nxt):
							ws = nxt
							nxt2 = ws.next_sibling
							if isinstance(nxt2, Tag) and emphasis_kind(nxt2) == kind:
								ws.extract()
								node.append(ws)
								for item in list(nxt2.contents):
									node.append(item)
								nxt2.decompose()
								continue
							break
						if isinstance(nxt, Tag) and emphasis_kind(nxt) == kind:
							for item in list(nxt.contents):
								node.append(item)
							nxt.decompose()
							continue
						break
				merge_adjacent_emphasis(node)
			node = node.next_sibling

	def wrap_emphasis(token, inner):
		if not inner:
			return ""
		lead_len = 0
		while lead_len < len(inner) and inner[lead_len].isspace():
			lead_len += 1
		trail_len = 0
		while trail_len < len(inner) - lead_len and inner[len(inner) - 1 - trail_len].isspace():
			trail_len += 1
		if lead_len == 0 and trail_len == 0:
			return f"{token}{inner}{token}"
		core_end = len(inner) - trail_len if trail_len else len(inner)
		core = inner[lead_len:core_end]
		if not core:
			return inner
		lead = inner[:lead_len]
		trail = inner[core_end:]
		return f"{lead}{token}{core}{token}{trail}"

	def walk(node):
		if isinstance(node, NavigableString):
			return str(node)
		if not isinstance(node, Tag):
			return ""
		name = node.name.lower()
		if name == "br":
			return " "
		inner = "".join(walk(child) for child in node.contents)
		if not inner:
			return ""
		if name in ("b", "strong"):
			return wrap_emphasis("**", inner)
		if name in ("i", "em"):
			return wrap_emphasis("*", inner)
		if name in ("s", "strike", "del"):
			return wrap_emphasis("~~", inner)
		if name in ("tt", "code"):
			return f"`{inner}`"
		if name == "a":
			href = node.get("href", "").strip()
			if href:
				return f"[{inner}]({href})"
			return inner
		return inner

	merge_adjacent_emphasis(soup)
	text = "".join(walk(child) for child in soup.contents)
	return normalize_ws(text)


def clean_code_line(text):
	text = text.replace("&quot", '"')
	text = html_lib.unescape(text)
	text = text.replace("\u00a0", " ")
	return text.rstrip("\n")


def fix_list_nesting(html):
	pattern = re.compile(
		r'(<li[^>]*>.*?</li>)\s*(<(ul|ol)[^>]*>.*?</\3>)',
		re.IGNORECASE | re.DOTALL,
	)
	prev = None
	while prev != html:
		prev = html
		html = pattern.sub(
			lambda m: re.sub(r'</li>\s*$', '', m.group(1), flags=re.IGNORECASE | re.DOTALL)
			+ m.group(2)
			+ "</li>",
			html,
		)
	return html


def replace_lists_with_markdown(html, create_placeholder, normalize_ws_func, strip_tags_func):
	tag_pattern = re.compile(r'<(ul|ol)\b[^>]*>', re.IGNORECASE)
	pos = 0
	out = []
	while True:
		match = tag_pattern.search(html, pos)
		if not match:
			out.append(html[pos:])
			break
		start = match.start()
		end = find_matching_list_end(html, match.start())
		if end is None:
			out.append(html[pos:])
			break
		out.append(html[pos:start])
		list_html = html[start:end]
		md_list = convert_list_to_markdown(list_html, normalize_ws_func, strip_tags_func, indent=0)
		out.append(create_placeholder("\n\n" + md_list + "\n\n"))
		pos = end
	return "".join(out)


def find_matching_list_end(html, start):
	tag_re = re.compile(r'<(/?)(ul|ol)\b[^>]*>', re.IGNORECASE)
	depth = 0
	for m in tag_re.finditer(html, start):
		if m.group(1) == "":
			depth += 1
		else:
			depth -= 1
			if depth == 0:
				return m.end()
	return None


def convert_list_to_markdown(list_html, normalize_ws_func, strip_tags_func, indent):
	tag_match = re.match(r'<(ul|ol)\b', list_html, re.IGNORECASE)
	if not tag_match:
		return ""
	list_tag = tag_match.group(1).lower()
	items = extract_list_items(list_html)
	lines = []
	index = 1
	for item_html in items:
		li_inner = re.sub(r'^<li[^>]*>|</li>$', '', item_html, flags=re.IGNORECASE | re.DOTALL)
		nested_lists = extract_nested_lists(li_inner)
		text_html = li_inner
		for _, nested_html in nested_lists:
			text_html = text_html.replace(nested_html, "")
		text = inline_html_to_markdown(text_html)
		if not text:
			continue
		if list_tag == "ol":
			prefix = f"{index}. "
			index += 1
		else:
			prefix = "- "
		lines.append(" " * indent + prefix + text)
		for _, nested_html in nested_lists:
			nested_md = convert_list_to_markdown(nested_html, normalize_ws_func, strip_tags_func, indent + 2)
			if nested_md:
				lines.append(nested_md)
	return "\n".join(lines)


def extract_list_items(list_html):
	li_re = re.compile(r'<li\b[^>]*>', re.IGNORECASE)
	tag_re = re.compile(r'</?li\b[^>]*>', re.IGNORECASE)
	items = []
	pos = 0
	while True:
		m = li_re.search(list_html, pos)
		if not m:
			break
		start = m.start()
		depth = 0
		for t in tag_re.finditer(list_html, start):
			if t.group(0).lower().startswith("<li"):
				depth += 1
			else:
				depth -= 1
				if depth == 0:
					end = t.end()
					items.append(list_html[start:end])
					pos = end
					break
		else:
			break
	return items


def extract_nested_lists(li_inner):
	nested = []
	tag_re = re.compile(r'<(ul|ol)\b[^>]*>', re.IGNORECASE)
	pos = 0
	while True:
		m = tag_re.search(li_inner, pos)
		if not m:
			break
		start = m.start()
		end = find_matching_list_end(li_inner, start)
		if end is None:
			break
		block = li_inner[start:end]
		nested.append((m.group(1).lower(), block))
		pos = end
	return nested


def detect_li_style(li_html):
	has_code = bool(re.search(r'<tt>|font[^>]*face="Courier"', li_html, re.IGNORECASE))
	has_strike = bool(re.search(r'<(strike|s|del)\b', li_html, re.IGNORECASE))
	has_bold = bool(re.search(r'<(b|strong)\b', li_html, re.IGNORECASE))
	has_italic = bool(re.search(r'<(i|em)\b', li_html, re.IGNORECASE))
	if has_code:
		return "code"
	if has_strike:
		return "strike"
	if has_bold and has_italic:
		return "bold_italic"
	if has_bold:
		return "bold"
	if has_italic:
		return "italic"
	return "plain"


def apply_li_style(text, style):
	if style == "code":
		return f"`{text}`"
	if style == "strike":
		return f"~~{text}~~"
	if style == "bold_italic":
		return f"***{text}***"
	if style == "bold":
		return f"**{text}**"
	if style == "italic":
		return f"*{text}*"
	return text


def rewrite_list_items(html, normalize_ws_func, strip_tags_func):
	pattern_li = re.compile(r'<li[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL)

	def replace_list_item(match):
		inner = match.group(1)
		if re.search(r'<(ul|ol)\b', inner, re.IGNORECASE):
			return match.group(0)
		inner_no_br = re.sub(r'<br\s*/?>', '', inner, flags=re.IGNORECASE)
		full_text = normalize_ws_func(strip_tags_func(inner_no_br))
		if not full_text:
			return match.group(0)

		link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', inner_no_br, re.IGNORECASE | re.DOTALL)
		if link_match:
			return f'<li><a href="{link_match.group(1)}">{strip_tags_func(link_match.group(2))}</a></li>'

		has_code = bool(re.search(r'<tt>|font[^>]*face="Courier"', inner_no_br, re.IGNORECASE))
		has_strike = bool(re.search(r'<(strike|s|del)\b', inner_no_br, re.IGNORECASE))
		has_bold = bool(re.search(r'<(b|strong)\b', inner_no_br, re.IGNORECASE))
		has_italic = bool(re.search(r'<(i|em)\b', inner_no_br, re.IGNORECASE))
		has_underline = bool(re.search(r'<u\b', inner_no_br, re.IGNORECASE))

		if has_code:
			return f"<li><code>{full_text}</code></li>"
		if has_strike:
			return f"<li><del>{full_text}</del></li>"
		if has_bold and has_italic:
			return f"<li><strong><em>{full_text}</em></strong></li>"
		if has_bold:
			return f"<li><strong>{full_text}</strong></li>"
		if has_italic:
			return f"<li><em>{full_text}</em></li>"
		if has_underline:
			return f"<li>{full_text}</li>"
		return match.group(0)

	return pattern_li.sub(replace_list_item, html)


def parse_blocks(html):
	tag_re = re.compile(r"<(div|ul|ol)\b", re.IGNORECASE)
	blocks = []
	pos = 0
	while True:
		m = tag_re.search(html, pos)
		if not m:
			break
		start = m.start()
		tag = m.group(1).lower()
		end = find_matching_tag_end(html, start, tag)
		if end is None:
			break
		block_html = html[start:end]
		if tag == "div":
			inner = re.sub(r"^<div[^>]*>|</div>$", "", block_html, flags=re.IGNORECASE | re.DOTALL)
			blocks.append({"type": "div", "html": block_html, "inner": inner})
		else:
			blocks.append({"type": tag, "html": block_html})
		pos = end
	return blocks


def find_matching_tag_end(html, start, tag):
	tag_re = re.compile(rf"<(/?){tag}\b[^>]*>", re.IGNORECASE)
	depth = 0
	for m in tag_re.finditer(html, start):
		if m.group(1) == "":
			depth += 1
		else:
			depth -= 1
			if depth == 0:
				return m.end()
	return None


def div_is_font_heading(inner, size_px):
	return bool(re.search(rf"font-size:\s*{size_px}px", inner, re.IGNORECASE))


def div_is_h3(inner):
	return bool(re.search(r"\(H3\)", inner, re.IGNORECASE))


def div_is_code_line(inner):
	return bool(re.search(r"<tt>.*?</tt>", inner, re.IGNORECASE | re.DOTALL))


def extract_code_line(inner):
	match = re.search(r"<tt>(.*?)</tt>", inner, re.IGNORECASE | re.DOTALL)
	if not match:
		return ""
	return clean_code_line(strip_tags(match.group(1)))


def div_contains_table(inner):
	return bool(re.search(r"<object>\s*<table", inner, re.IGNORECASE))


def convert_table_from_div(inner):
	match = re.search(r"<object>\s*(<table[^>]*>.*?</table>)\s*</object>", inner, re.IGNORECASE | re.DOTALL)
	if not match:
		return ""
	return convert_table_html(match.group(1))


def convert_table_html(table_html):
	rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.IGNORECASE | re.DOTALL)
	if not rows:
		return ""
	parsed = []
	header_cells_html = None
	max_cols = 0
	for row_idx, row in enumerate(rows):
		cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.IGNORECASE | re.DOTALL)
		if not cells:
			continue
		texts = [normalize_ws(strip_tags(c)) for c in cells]
		parsed.append(texts)
		max_cols = max(max_cols, len(texts))
		if row_idx == 0:
			header_cells_html = cells
	if not parsed:
		return ""
	for row in parsed:
		if len(row) < max_cols:
			row.extend([""] * (max_cols - len(row)))
	header = parsed[0]
	aligns = [":---:"] * max_cols
	lines = [
		"| " + " | ".join(header) + " |",
		"| " + " | ".join(aligns) + " |",
	]
	for row in parsed[1:]:
		lines.append("| " + " | ".join(row) + " |")
	return "\n".join(lines)


def div_has_bold(inner):
	return bool(re.search(r"<(b|strong)\b", inner, re.IGNORECASE))


def div_has_italic(inner):
	return bool(re.search(r"<(i|em)\b", inner, re.IGNORECASE))


def div_has_strike(inner):
	return bool(re.search(r"<(strike|s|del)\b", inner, re.IGNORECASE))


def div_has_underline(inner):
	return bool(re.search(r"<u\b", inner, re.IGNORECASE))


def div_has_code(inner):
	return bool(re.search(r"<tt\b|font[^>]*face=\"Courier\"", inner, re.IGNORECASE))


def div_has_list(inner):
	return bool(re.search(r"<(ul|ol|li)\b", inner, re.IGNORECASE))


def div_has_table(inner):
	return bool(re.search(r"<(table|object)\b", inner, re.IGNORECASE))


def div_is_bold_italic_line(inner):
	if not (div_has_bold(inner) and div_has_italic(inner)):
		return False
	if div_has_strike(inner) or div_has_underline(inner) or div_has_code(inner):
		return False
	if div_has_list(inner) or div_has_table(inner):
		return False
	return True


def div_is_bold_strike_line(inner):
	if not (div_has_bold(inner) and div_has_strike(inner)):
		return False
	if div_has_italic(inner) or div_has_underline(inner) or div_has_code(inner):
		return False
	if div_has_list(inner) or div_has_table(inner):
		return False
	return True


def div_is_italic_strike_line(inner):
	if not (div_has_italic(inner) and div_has_strike(inner)):
		return False
	if div_has_bold(inner) or div_has_underline(inner) or div_has_code(inner):
		return False
	if div_has_list(inner) or div_has_table(inner):
		return False
	return True


def div_is_strike_line(inner):
	if not div_has_strike(inner):
		return False
	if div_has_bold(inner) or div_has_italic(inner) or div_has_underline(inner) or div_has_code(inner):
		return False
	if div_has_list(inner) or div_has_table(inner):
		return False
	return True


def div_is_italic_line(inner):
	if not div_has_italic(inner):
		return False
	if div_has_bold(inner) or div_has_strike(inner) or div_has_underline(inner) or div_has_code(inner):
		return False
	if div_has_list(inner) or div_has_table(inner):
		return False
	return True


def div_is_bold_only(inner):
	temp = re.sub(r"<b[^>]*>.*?</b>", "", inner, flags=re.IGNORECASE | re.DOTALL)
	temp = re.sub(r"<br\s*/?>", "", temp, flags=re.IGNORECASE)
	temp = strip_tags(temp)
	return normalize_ws(temp) == ""


def strip_hidden_marker(html, marker):
	pattern = re.compile(
		r'<div[^>]*style="[^"]*display\s*:\s*none[^"]*"[^>]*>\s*'
		+ re.escape(marker)
		+ r'\s*</div>',
		re.IGNORECASE | re.DOTALL,
	)
	return pattern.sub("", html)


def html_to_markdown(html, marker=None):
	html_body = strip_embedded_markdown(html)
	if marker:
		html_body = strip_hidden_marker(html_body, marker)
	html_body = fix_list_nesting(html_body)
	blocks = parse_blocks(html_body)
	md_parts = []
	i = 0
	while i < len(blocks):
		block = blocks[i]
		if block["type"] in {"ul", "ol"}:
			md_list = convert_list_to_markdown(block["html"], normalize_ws, strip_tags, indent=0)
			if md_list:
				md_parts.append(md_list)
			i += 1
			continue
		if block["type"] != "div":
			i += 1
			continue
		inner = block["inner"]
		if div_contains_table(inner):
			md_table = convert_table_from_div(inner)
			if md_table:
				md_parts.append(md_table)
			i += 1
			continue
		if div_is_font_heading(inner, 24):
			md_parts.append(f"# {normalize_ws(strip_tags(inner))}")
			i += 1
			continue
		if div_is_font_heading(inner, 18):
			md_parts.append(f"## {normalize_ws(strip_tags(inner))}")
			i += 1
			continue
		if div_is_h3(inner):
			md_parts.append(f"### {normalize_ws(strip_tags(inner))}")
			i += 1
			continue
		if div_is_code_line(inner):
			code_lines = []
			while i < len(blocks) and blocks[i]["type"] == "div" and div_is_code_line(blocks[i]["inner"]):
				line = extract_code_line(blocks[i]["inner"])
				if line:
					code_lines.append(line)
				i += 1
			if code_lines:
				md_parts.append("```\n" + "\n".join(code_lines) + "\n```")
			continue
		text = inline_html_to_markdown(inner)
		if text:
			md_parts.append(text)
		i += 1
	return normalize_markdown("\n\n".join(md_parts))


def normalize_markdown(md):
	md = md.replace("\u00a0", " ")
	md = re.sub(r"(?m)^\s*\*\*\s*\*\*\s*$", "", md)
	md = re.sub(r"(?m)^\s*__\s*__\s*$", "", md)
	md = normalize_emphasis(md)
	md = dedent_list_items(md)
	md = merge_adjacent_bold(md)
	md = re.sub(r"(?m)^(#{1,6} .+)\n\s*\n(?=#{1,6} )", r"\1\n", md)
	md = re.sub(r"(?m)^[ \t]+$", "", md)
	md = re.sub(r"\n{3,}", "\n\n", md)
	return md.strip()


def normalize_emphasis(md):
	md = re.sub(r"\*\*_([^*\n]+)_\*\*", r"***\1***", md)
	md = re.sub(r"__\*([^*\n]+)\*__", r"***\1***", md)
	md = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"*\1*", md)
	return md



def dedent_list_items(md):
	lines = md.splitlines()
	out = []
	in_fence = False
	i = 0
	while i < len(lines):
		line = lines[i]
		stripped = line.lstrip()
		if stripped.startswith("```"):
			in_fence = not in_fence
			out.append(line)
			i += 1
			continue
		if in_fence or not re.match(r"^\s*([-*+] |\d+\. )", line):
			out.append(line)
			i += 1
			continue
		block_start = i
		min_indent = None
		while i < len(lines):
			cur = lines[i]
			cur_strip = cur.lstrip()
			if cur_strip.startswith("```"):
				break
			if cur.strip() == "":
				i += 1
				continue
			if not re.match(r"^\s*([-*+] |\d+\. )", cur):
				break
			indent = len(cur) - len(cur.lstrip(" "))
			min_indent = indent if min_indent is None else min(min_indent, indent)
			i += 1
		if min_indent is None:
			out.append(lines[block_start])
			i = block_start + 1
			continue
		for j in range(block_start, i):
			cur = lines[j]
			if cur.strip() == "":
				out.append(cur)
				continue
			if re.match(r"^\s*([-*+] |\d+\. )", cur):
				out.append(cur[min_indent:])
			else:
				out.append(cur)
	return "\n".join(out)


def merge_adjacent_bold(md):
	prev = None
	while prev != md:
		prev = md
		md = re.sub(r"\*\*([^*\n]+)\*\*[ \t]*\*\*([:：,，.!?？！])\*\*", r"**\1\2**", md)
		md = re.sub(r"\*\*([^*\n]+)\*\*[ \t]*\*\*([^*\n]+)\*\*", r"**\1 \2**", md)
	return md


def markdown_to_html(md):
	extras = [
		"fenced-code-blocks",
		"tables",
		"strike",
		"task_list",
		"cuddled-lists",
		"code-friendly",
	]
	return markdown2.markdown(md, extras=extras)


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


def notes_html_to_markdown(html, cache_key=None, force_html=False):
	if not html:
		return ""
	if force_html:
		return html_to_markdown(html)
	if cache_key:
		cached = read_cache_markdown(cache_key)
		if cached is not None:
			return cached.strip()
	embedded = extract_embedded_markdown(html)
	if embedded is not None:
		return embedded.strip()
	md = html_to_markdown(html)
	if cache_key:
		write_cache_markdown(cache_key, md)
	return md


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


def _fetch_notes_snapshot():
	script = """
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
	result = subprocess.run(
		["osascript", "-e", script],
		capture_output=True,
		text=True,
		check=False,
	)
	if result.returncode != 0:
		message = result.stderr.strip() or "Unknown AppleScript error."
		raise RuntimeError(message)
	raw = result.stdout.rstrip("\n")
	return _parse_notes_raw(raw)


def _write_notes_cache(notes, cache_path=NOTES_CACHE_PATH):
	dir_path = os.path.dirname(cache_path)
	if dir_path and not os.path.exists(dir_path):
		os.makedirs(dir_path, exist_ok=True)
	notes_summary = []
	for note in notes:
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		notes_summary.append({"folder": folder, "title": title})
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
		return [], "Notes cache not ready."
	except Exception as exc:
		return [], f"Notes cache read failed: {exc}"
	if isinstance(payload, dict):
		notes = payload.get("notes", [])
	elif isinstance(payload, list):
		notes = payload
	else:
		notes = []
	return notes, None


class NotesCacheWorker(QThread):
	error = pyqtSignal(str)
	updated = pyqtSignal(int)

	def __init__(self, cache_path=NOTES_CACHE_PATH, parent=None):
		super().__init__(parent)
		self.cache_path = cache_path
		self._running = True

	def stop(self):
		self._running = False

	def run(self):
		while self._running:
			try:
				parent = self.parent()
				if parent and getattr(parent, "notes_refresh_in_progress", False):
					interval = self._next_interval_seconds()
					steps = max(1, int(interval / 0.1))
					for _ in range(steps):
						if not self._running:
							return
						time.sleep(0.1)
					continue
				notes = _fetch_notes_snapshot()
				_write_notes_cache(notes, self.cache_path)
				self.updated.emit(len(notes))
			except Exception as exc:
				self.error.emit(str(exc))
			interval = self._next_interval_seconds()
			steps = max(1, int(interval / 0.1))
			for _ in range(steps):
				if not self._running:
					return
				time.sleep(0.1)

	def _next_interval_seconds(self):
		try:
			active_app = NSWorkspace.sharedWorkspace().activeApplication()
			app_name = active_app.get("NSApplicationName", "")
		except Exception:
			app_name = ""
		if app_name == "Watermelon":
			return 5
		return 30


class NotesLoader(QThread):
	finished = pyqtSignal(list)
	error = pyqtSignal(str)

	def run(self):
		script = """
		set AppleScript's text item delimiters to ASCII character 31
		tell application "Notes"
			set outList to {}
			repeat with n in notes
				set t to name of n
				set b to body of n
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
		try:
			result = subprocess.run(
				["osascript", "-e", script],
				capture_output=True,
				text=True,
				check=False,
			)
		except Exception as exc:
			self.error.emit(f"Failed to run osascript: {exc}")
			return

		if result.returncode != 0:
			message = result.stderr.strip() or "Unknown AppleScript error."
			self.error.emit(message)
			return

		raw = result.stdout.rstrip("\n")
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
		self.finished.emit(notes)


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
			if self.render_left:
				left_html = markdown_to_html(self.markdown_text)
			if self.isInterruptionRequested():
				return
			if self.render_right:
				bio_md = _bionic_transform_text(self.markdown_text.replace('*', ''))
				if self.isInterruptionRequested():
					return
				right_html = markdown_to_html(bio_md)
			if self.isInterruptionRequested():
				return
			self.rendered.emit(self.request_id, left_html, right_html)
		except Exception as exc:
			self.failed.emit(self.request_id, str(exc))


class NotesFolderDialog(CustomMessageBox):
	note_selected = pyqtSignal(object)

	def __init__(self):
		super().__init__(text=None, buttons=(), fixed_size=None)
		self.radius = 16  # 圆角半径，可按 macOS 15 或 26 设置为 16~26

		self.setWindowTitle("Select Notes")
		self.center()
		self.resize(520, 320)
		self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
		# self._centered_once = False
		self.body_layout.setContentsMargins(20, 28, 20, 20)
		self.body_layout.setSpacing(12)

		self.notes = []
		self.filtered_notes = []
		self.folder_ids = []
		self.active_folder = None

		self.status_label = QLabel("Ready.")
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("Filter notes by title...")
		self.search_input.textChanged.connect(self.apply_filter)

		self.folder_list = QListWidget()
		self.folder_list.currentRowChanged.connect(self.on_folder_changed)

		self.list_widget = QListWidget()
		self.list_widget.itemDoubleClicked.connect(self.select_current)

		splitter = QSplitter(Qt.Orientation.Horizontal)
		splitter.addWidget(self.folder_list)
		splitter.addWidget(self.list_widget)
		splitter.setStretchFactor(0, 1)
		splitter.setStretchFactor(1, 2)

		select_btn = WhiteButton("Select")
		# select_btn.setFixedSize(100, 20)
		select_btn.clicked.connect(self.select_current)
		cancel_btn = WhiteButton("Cancel")
		# cancel_btn.setFixedSize(100, 20)
		cancel_btn.clicked.connect(self.reject)

		btn_row = QHBoxLayout()
		btn_row.setContentsMargins(0, 0, 0, 0)
		btn_row.addStretch()
		btn_row.addWidget(select_btn)
		btn_row.addWidget(cancel_btn)
		btn_row.addStretch()

		w3 = QWidget()
		blay3 = QVBoxLayout()
		blay3.setContentsMargins(20, 20, 20, 20)
		blay3.addWidget(self.status_label)
		blay3.addWidget(self.search_input)
		blay3.addWidget(splitter)
		blay3.addLayout(btn_row)
		w3.setLayout(blay3)
		#w3.setObjectName("Main")

		self.body_layout.addWidget(w3)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

		rect = QRectF(self.rect())
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)

		painter.setClipPath(path)
		bg_color = self.palette().color(QPalette.ColorRole.Window)
		painter.fillPath(path, bg_color)

	# 让无边框窗口可拖动
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.drag_pos)
			event.accept()

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

	def set_status(self, text):
		self.status_label.setText(text)

	def set_notes(self, notes):
		self.notes = notes
		self.populate_folders()
		self.apply_filter(self.search_input.text())
		if notes:
			self.set_status("Select a note:")
		else:
			self.set_status("No notes found.")

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
		self.folder_list.addItem("All Notes")
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

	def apply_filter(self, text):
		query = text.strip().lower()
		self.filtered_notes = []
		for note in self.notes:
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


class window3(QWidget):  # 主窗口
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
		self.update_check_worker = None
		self.auto_update_check_enabled = load_auto_update_check_enabled()
		self.update_alert_dedupe_enabled = load_update_alert_dedupe_enabled()
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
		self._update_notice_box = None
		self._last_notified_update_version = None
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

		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
					border-image: url(/Applications/Watermelon.app/Contents/Resources/middle6.png);
					height: 20px;
					border-radius: 4px;
					}
					''')
		self.splitter1.setStyleSheet('''
					QSplitter::handle{
					border: transparent;
					background-color: transparent;
					border-image: url(/Applications/Watermelon.app/Contents/Resources/middle2.png);
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

		self.btn_sub1 = MacNormalButton('Open', self, always_dark=True)
		self.btn_sub1.clicked.connect(self.open_file)
		self.btn_sub1.setFixedSize(210, 22)
		self.btn_sub2 = MacNormalButton('New', self, always_dark=True)
		self.btn_sub2.clicked.connect(self.new_file)
		self.btn_sub2.setFixedSize(210, 22)

		self.widget0 = DropdownButton(self, always_dark=True)
		self.widget0.setCurrentIndex(0)
		self.widget0.setFixedSize(210, 22)
		self.widget0.setFixedWidth(210)
		tarname3 = "Note 001.md"
		fulldir3 = os.path.join(fulldir1, tarname3)
		if not os.path.exists(fulldir3):
			with open(fulldir3, 'a', encoding='utf-8') as f0:
				f0.write('''This is your very first note stored in [Home]/WatermelonAppPath/Note 001.md. 

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

		self.btn_notes_folder = MacNormalButton('Notes Folder', self, always_dark=True)
		self.btn_notes_folder.clicked.connect(self.open_notes_folder_dialog)
		self.btn_notes_folder.setFixedSize(210, 22)

		self.widget_notes = DropdownButton(self, always_dark=True)
		self.widget_notes.setFixedSize(210, 22)
		self.widget_notes.setFixedWidth(210)
		self.widget_notes.setEnabled(False)
		self.widget_notes.currentIndexChanged.connect(self.notes_index_change)

		self.btn_notes_save = MacNormalButton('Save', self, always_dark=True)
		self.btn_notes_save.clicked.connect(self.save_notes_sync)
		self.btn_notes_save.setFixedSize(210, 22)
		self.btn_notes_save.setEnabled(False)

		self.btn_notes_new = MacNormalButton('New', self, always_dark=True)
		self.btn_notes_new.clicked.connect(self.new_notes_note)
		self.btn_notes_new.setFixedSize(210, 22)
		self.btn_notes_new.setEnabled(False)

		self.btn_notes_export = MacNormalButton('Export', self, always_dark=True)
		self.btn_notes_export.clicked.connect(self.export_notes_file)
		self.btn_notes_export.setFixedSize(210, 22)
		self.btn_notes_export.setEnabled(False)

		self.btn_sub3 = MacNormalButton('Export', self, always_dark=True)
		self.btn_sub3.clicked.connect(self.export_file)
		self.btn_sub3.setFixedSize(210, 22)

		self.btn_sub4 = MacNormalButton('Clear', self, always_dark=True)
		self.btn_sub4.clicked.connect(self.clear_all)
		self.btn_sub4.setFixedSize(210, 22)

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
		hbox1.addWidget(self.btn_notes_save)
		hbox1.addWidget(self.btn_sub3)
		hbox1.addWidget(self.btn_sub4)
		hbox1.addStretch()
		self.qw1.setLayout(hbox1)

		vbox3 = QVBoxLayout()
		vbox3.setContentsMargins(0, 0, 0, 0)
		vbox3.addWidget(self.qw0)
		vbox3.addStretch()
		vbox3.addWidget(self.qw1)
		vbox3.addStretch()
		self.setLayout(vbox3)

		self.btn_00 = WhiteButton('', self)
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
			icon_path='/Applications/Watermelon.app/Contents/Resources/set2.png',
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
			icon_path='/Applications/Watermelon.app/Contents/Resources/repeat.png',
			momentary=True,
			parent=self
		)
		self.btn0_2.setFixedSize(38, 38)
		self.btn0_2.move(1324, SCREEN_HEIGHT - 70)

		self.btn0_sound = GlassButton(
			'', radius=19,
			icon_path='/Applications/Watermelon.app/Contents/Resources/speaker.png',
			momentary=True,
			parent=self
		)
		self.btn0_sound.setFixedSize(38, 38)
		self.btn0_sound.move(1383, SCREEN_HEIGHT - 200)
		self.btn0_sound.clicked.connect(self.toggle_sound_mode)
		self._start_sound_monitor()

		self._apply_mode_visibility()

		currentfile = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
		try:
			targetpath = pathslist[currentfile].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
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

		# 启动内部组件动画（延迟一小段时间让窗口先开始滑入）
		QTimer.singleShot(200, self._start_intro_animation)

		# self.assigntoall()

		# w2.checkupdate()
		# if w2.lbl2.text() != 'No Intrenet' and 'ready' in w2.lbl2.text():
		# 	w2.show()

		# 启动后稍等再开始自动更新检查，避免启动期焦点/模态竞争
		self.set_update_alert_dedupe_enabled(self.update_alert_dedupe_enabled)
		QTimer.singleShot(1800, self._start_auto_update_check_after_startup)
		self._start_mode_autobackup()

	def showEvent(self, event):
		super().showEvent(event)
		self._connect_screen_signals()

	def changeEvent(self, event):
		super().changeEvent(event)
		# 当窗口被激活时（用户从其他应用切换回来），检查 Notes 路径是否有效
		if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
			self._check_notes_path_on_focus()

	def _check_notes_path_on_focus(self):
		"""当窗口获得焦点时，检查当前 Notes 路径是否仍然有效"""
		if not self.notes_mode_enabled or not self.notes_active:
			return
		if self.notes_awaiting_reselect:
			return  # 已经在等待用户重新选择，不重复检查
		if not self.notes_current_folder or not self.notes_current_title:
			return
		# 检查路径是否有效
		check_html = self._read_note_html(self.notes_current_folder, self.notes_current_title)
		if check_html is None or not check_html.strip():
			# 路径无效，锁定编辑器并提示用户
			self._set_notes_active(False)
			self._prompt_notes_reselect(self.notes_current_folder, self.notes_current_title)

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

	def _update_word_count_label(self):
		if not hasattr(self, "bottom") or not hasattr(self, "word_count_label"):
			return
		if not self._has_active_document_for_word_count():
			self.word_count_label.hide()
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
				f"Selected: {selected_chars} chars, {selected_words} words | "
				f"Total: {total_chars} chars, {total_words} words"
			)
		else:
			self.word_count_label.setText(f"Total: {total_chars} chars, {total_words} words")
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
			value = codecs.open(BasePath + 'always_on_top.txt', 'r', encoding='utf-8').read().strip()
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
			with open(BasePath + 'always_on_top.txt', 'w', encoding='utf-8') as f0:
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
		animation.start()
		self.i += 1

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
		fade_widgets = [self.qw1, self.btn_00, self.btn0_1, self.btn0_2, self.btn0_sound, self.word_count_label]

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

		self._fade_group.finished.connect(self._on_intro_animation_finished)
		self._fade_group.start()

	def _on_intro_animation_finished(self):
		"""启动动画完成后的清理工作"""
		# 移除透明度效果，恢复正常渲染
		for widget in [self.qw1, self.btn_00, self.btn0_1, self.btn0_2, self.btn0_sound, self.word_count_label]:
			widget.setGraphicsEffect(None)
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
		fade_widgets = [self.qw1, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn_00, self.word_count_label]

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

		self._hide_anim_group.finished.connect(self._on_pin_hide_animation_finished)
		self._hide_anim_group.start()

	def _on_pin_hide_animation_finished(self):
		"""隐藏动画完成后的清理和回调"""
		# 移除透明度效果（包括 btn_00）
		for widget in [self.qw1, self.btn0_1, self.btn0_2, self.btn0_sound, self.btn_00, self.word_count_label]:
			widget.setGraphicsEffect(None)

		# 隐藏组件
		self.qw0.setVisible(False)
		self.qw1.setVisible(False)
		self.l1.setVisible(False)
		self.btn_00.setVisible(False)
		self.btn0_1.setVisible(False)
		self.btn0_sound.setVisible(False)
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

	def assigntoall(self):
		cmd = '''on run
			tell application "System Events" to set activeApp to "Watermelon"
			tell application "System Events" to tell UI element activeApp of list 1 of process "Dock"
				perform action "AXShowMenu"
				click menu item "Options" of menu 1
				click menu item "All Desktops" of menu 1 of menu item "Options" of menu 1
			end tell
		end run'''
		try:
			subprocess.call(['osascript', '-e', cmd])
		except Exception as e:
			pass

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
			self.word_count_label.setVisible(False)
			self.updatecontent_for_mode()
			# 用 QTimer 延迟恢复透明度，确保隐藏操作已生效
			def restore_and_animate():
				self.setWindowOpacity(1)
				self._start_pin_show_animation(SCREEN_HEIGHT)
			QTimer.singleShot(50, restore_and_animate)
		if self.i % 2 == 0:  # hide
			if self.notes_mode_enabled and self.notes_dirty:
				user_choice = self._confirm_notes_save()
				if user_choice == "cancel":
					return
				if user_choice == "save":
					self.save_notes_sync()
					if self.notes_dirty:
						return
				if user_choice == "discard":
					self._set_notes_dirty(False)
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

	def toggle_sound_mode(self):
		self.sound_mode_enabled = not self.sound_mode_enabled
		if self.sound_mode_enabled:
			self._show_mode_toast("Sound ON")
		else:
			self._show_mode_toast("Sound OFF")

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
				if not w3_ref.sound_mode_enabled or not w3_ref.bottom.hasFocus():
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
					if chars and len(chars) > 0 and ord(chars[0]) >= 32 and ord(chars[0]) < 0xF700:
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
		self._stop_update_check_worker()
		if self._update_notice_box is not None:
			try:
				self._update_notice_box.close()
			except Exception:
				pass
			self._update_notice_box = None
		self._stop_preview_rendering()
		self._stop_sound_monitor()
		self._stop_notes_wait()
		if self.notes_cache_worker:
			self.notes_cache_worker.stop()
			self.notes_cache_worker.wait(2000)
		event.accept()

	def resizeEvent(self, event):
		super().resizeEvent(event)
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
			with open(os.path.join(BasePath, "layout_debug.log"), "a", encoding="utf-8") as f0:
				f0.write(line)
			if self.qw0.isVisible() and new_size.width() not in (100, 1520):
				stack = "".join(traceback.format_stack(limit=12))
				with open(os.path.join(BasePath, "layout_debug.log"), "a", encoding="utf-8") as f0:
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
				self.topleft.setHtml("")
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
		app_dir = os.path.join(home_dir, "WatermelonAppPath")
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

	def _perform_mode_backup(self, target_dir, content):
		with self._mode_backup_lock:
			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
			backup_path = os.path.join(target_dir, f"{timestamp}.md")
			try:
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
				if f.endswith('.md')
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
			with open(source_path, 'r', encoding='utf-8') as fp:
				content = fp.read()
		except Exception:
			return
		label = Path(source_path).stem
		target_dir = self._backup_target_dir(self.local_mode_backup_root, label, source_path)
		threading.Thread(
			target=self._perform_mode_backup,
			args=(target_dir, content),
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
		box = CustomMessageBox(
			text=text,
			parent=self,
			buttons=buttons,
			default=default,
		)
		box.setWindowTitle(title)
		result = box.exec()
		return result if result is not None else -1

	def _confirm_notes_save(self):
		box = CustomMessageBox(
			text="Save changes to this note?",
			parent=self,
			buttons=("Save", "Discard", "Cancel"),
			default=0,
		)
		box.setWindowTitle("Unsaved Notes")
		for btn in box.btns:
			btn.setFixedWidth(100)
		result = box.exec()
		result = result if result is not None else -1
		if result == 0:
			return "save"
		if result == 1:
			return "discard"
		return "cancel"

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

	def _confirm_notes_title_change(self, old_title, new_title):
		result = self._show_custom_message_box(
			title="Note Title Changed",
			text=f"The note title will change from \"{old_title}\" to \"{new_title}\".\nContinue saving?",
			buttons=("Save", "Cancel"),
			default=0,
		)
		return result == 0

	def _prompt_notes_reselect(self, folder, title):
		# 如果已经在等待用户重新选择，不要重复弹窗
		if self.notes_awaiting_reselect:
			return
		# 确保 bottom 被锁定
		self._set_notes_active(False)
		location = folder or "Unfiled"
		result = self._show_custom_message_box(
			title="Note Not Found",
			text=(
				f"Couldn't match the current note \"{title}\" in \"{location}\".\n"
				"Please reselect the note path."
			),
			buttons=("OK", "Cancel"),
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
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
			previewtext = codecs.open(current_path, 'r', encoding='utf-8').read()
			self.widget0.setCurrentIndex(current_index)
		except Exception as e:
			with open(fulldir4, 'w', encoding='utf-8') as f0:
				f0.write('0')
			targetpath = pathslist[0].split('||')[1]
			previewtext = codecs.open(targetpath, 'r', encoding='utf-8').read()
			currentindex = int(codecs.open(fulldir4, 'r', encoding='utf-8').read())
			self.widget0.setCurrentIndex(currentindex)
		pos = int(codecs.open(BasePath + 'text_position.txt', 'r', encoding='utf-8').read())
		self.bottom.setText(previewtext)
		self.bottom.ensureCursorVisible()  # 游标可用
		cursor = self.bottom.textCursor()  # 设置游标
		cursor.setPosition(pos)  # 游标位置设置为尾部
		self.bottom.setTextCursor(cursor)  # 滚动到游标位置
		self._request_async_preview_render(previewtext, debounce_ms=0)

	def _request_async_preview_render(self, markdown_text, debounce_ms=90):
		self._update_word_count_label()
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
			self.topleft.setHtml(self.md2html("", pre_rendered_html=left_markdown_html))
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
			return int(codecs.open(BasePath + 'fs.txt', 'r', encoding='utf-8').read())
		except Exception:
			return default

	def _resolve_font_family(self, fallback="Times New Roman"):
		try:
			font_family = codecs.open(BasePath + 'lastused.txt', 'r', encoding='utf-8').read()
		except Exception:
			return fallback
		if font_family == '0':
			font_path = BasePath + "chillduanheisong_widelight.otf"
			font_id = QFontDatabase.addApplicationFont(font_path)
			if font_id != -1:
				families = QFontDatabase.applicationFontFamilies(font_id)
				if families:
					return families[0]
			return fallback
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
		if self.bottom.toPlainText() != '':
			# set text
			home_dir = str(Path.home())
			tarname1 = "WatermelonAppPath"
			fulldir1 = os.path.join(home_dir, tarname1)
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
		with open(BasePath + 'text_position.txt', 'w', encoding='utf-8') as f0:
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
		fj = QFileDialog.getOpenFileName(self, "Open File", home_dir, "Markdown Files (*.md)")
		if fj[0] != '':
			str_fj = ''.join(fj)
			str_fj = str_fj.replace('Markdown Files (*.md)', '')
			text_open = codecs.open(str_fj, 'r', encoding='utf-8').read()
			# set list
			tarname1 = "WatermelonAppPath"
			fulldir1 = os.path.join(home_dir, tarname1)
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
		self.topleft.setHtml("")
		self.topright.clear()

		current_time = datetime.now().strftime('%Y-%m-%d %f')
		newfile_name = 'Note ' + current_time
		newfile_name_full = 'Note ' + current_time + ".md"
		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
		self.topleft.setHtml("")
		self.topright.clear()

		# set text
		current_index = i
		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
			previewtext = codecs.open(current_path, 'r', encoding='utf-8').read()
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

	def _set_notes_dirty(self, dirty):
		self.notes_dirty = bool(dirty)
		if hasattr(self.btn_notes_save, "set_alert"):
			self.btn_notes_save.set_alert(self.notes_dirty)
		else:
			if self.notes_dirty:
				self.btn_notes_save.setStyleSheet('''
					QPushButton{
					border: 1px outset grey;
					background-color: #FF4D4D;
					border-radius: 4px;
					padding: 1px;
					color: #FFFFFF
					}
					QPushButton:pressed{
					border: 1px outset grey;
					background-color: #CC3D3D;
					border-radius: 4px;
					padding: 1px;
					color: #FFFFFF
					}
					QPushButton:disabled{
					border: 1px solid #999999;
					background-color: #E6E6E6;
					border-radius: 4px;
					padding: 1px;
					color: #777777
					}
					''')
			else:
				self.btn_notes_save.setStyleSheet('''
					QPushButton:disabled{
					border: 1px solid #999999;
					background-color: #E6E6E6;
					border-radius: 4px;
					padding: 1px;
					color: #777777
					}
					''')

	def _set_notes_active(self, active):
		self.notes_active = bool(active)
		self.btn_notes_save.setEnabled(self.notes_active)
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
			with open(os.path.join(BasePath, "layout_debug.log"), "a", encoding="utf-8") as f0:
				f0.write(line)
		except Exception:
			pass

	def _apply_mode_visibility(self):
		self.qw1.setUpdatesEnabled(False)
		if self.notes_mode_enabled:
			for widget in (self.btn_sub1, self.btn_sub2, self.widget0, self.btn_sub3, self.btn_sub4):
				widget.setVisible(False)
			for widget in (self.btn_notes_folder, self.widget_notes, self.btn_notes_save, self.btn_notes_new, self.btn_notes_export):
				widget.setVisible(True)
		else:
			for widget in (self.btn_notes_folder, self.widget_notes, self.btn_notes_save, self.btn_notes_new, self.btn_notes_export):
				widget.setVisible(False)
			for widget in (self.btn_sub1, self.btn_sub2, self.widget0, self.btn_sub3, self.btn_sub4):
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
			self.widget_notes.setCurrentIndex(target_index)
		else:
			self.widget_notes.setEnabled(False)
			self._set_notes_active(False)
			self.notes_force_reload = False
			self.bottom.blockSignals(True)
			self.bottom.clear()
			self.bottom.blockSignals(False)
			self.topleft.setHtml("")
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
			self.notes_wait_dialog = CustomMessageBox(
				"Updating Notes, please wait...",
				parent=self,
				buttons=(),
				fixed_size=(260, 90),
			)
			self.notes_wait_dialog.setWindowTitle("Updating Notes")
			self.notes_wait_dialog.setWindowFlags(
				self.notes_wait_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
			)
			self.notes_wait_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
			self.notes_wait_dialog.destroyed.connect(self._notes_wait_dialog_destroyed)
			self.notes_wait_dialog.body_layout.setContentsMargins(20, 28, 20, 20)
			# 居中显示
			screen = QGuiApplication.primaryScreen()
			if screen:
				geo = screen.availableGeometry()
				x = geo.x() + (geo.width() - 260) // 2
				y = geo.y() + (geo.height() - 90) // 2
				self.notes_wait_dialog.move(x, y)
		self.notes_wait_dialog.show()
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

	def _read_note_html(self, folder, title):
		script = r'''
		on run argv
			set targetFolder to item 1 of argv
			set targetTitle to item 2 of argv
			tell application "Notes"
				set targetNote to missing value
				repeat with n in notes
					set t to name of n
					if t is equal to targetTitle then
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
						if targetFolder is "" then
							set targetNote to n
							exit repeat
						end if
						if f is equal to targetFolder then
							set targetNote to n
							exit repeat
						end if
					end if
				end repeat
				if targetNote is missing value then
					return ""
				end if
				return body of targetNote
			end tell
		end run
		'''
		try:
			result = subprocess.check_output(["osascript", "-e", script, folder, title], text=True)
		except Exception:
			return ""
		return result

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
		self.notes_mode_enabled = not self.notes_mode_enabled
		if self.notes_mode_enabled:
			# self.btn_mode.setText('Mode: Notes')
			self.btn0_2.setIconPath('/Applications/Watermelon.app/Contents/Resources/repeat2.png')
		else:
			# self.btn_mode.setText('Mode: Local')
			self.btn0_2.setIconPath('/Applications/Watermelon.app/Contents/Resources/repeat.png')
			self._set_notes_active(False)
			# 切换回普通模式时，恢复 bottom 为可编辑状态
			self.bottom.setReadOnly(False)
		self._apply_mode_visibility()
		self.updatecontent_for_mode()
		self._update_word_count_label()
		QTimer.singleShot(50, lambda: self._log_layout_state("toggle_after"))
		# 显示模式切换提示
		mode_name = "Notes Mode" if self.notes_mode_enabled else "Local Mode"
		self._show_mode_toast(mode_name)

	def toggle_teleprompter(self):
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

			self._show_mode_toast("Teleprompter")
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

			self._show_mode_toast("Normal Mode")
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
			check_html = self._read_note_html(self.notes_current_folder, self.notes_current_title)
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
				self.topleft.setHtml("")
				self.topright.clear()

	def new_notes_note(self):
		if not self.notes_mode_enabled:
			return
		folder = self.notes_current_folder or ""
		now_str = datetime.now().strftime('%Y-%m-%d %H%M%S')
		title = f"Note {now_str}"
		note_md = ""
		note_html = markdown_to_html(note_md)
		note_html = embed_markdown(note_html, note_md)
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
				if targetFolder is "" or targetFolder is "Unfiled" then
					set theNote to make new note with properties {name:targetTitle, body:newHTML}
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
						set theNote to make new note at theAcct with properties {name:targetTitle, body:newHTML}
					else
						set theNote to make new note at folder folderName of theAcct with properties {name:targetTitle, body:newHTML}
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
						set theNote to make new note with properties {name:targetTitle, body:newHTML}
					else
						set theNote to make new note at theFolder with properties {name:targetTitle, body:newHTML}
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
		result = subprocess.check_output(["osascript", "-e", script, folder, title, path], text=True)
		return result.strip()

	def export_notes_file(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
		if fj != '':
			title = self.widget_notes.currentText().strip() or "Note"
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

	def notes_index_change(self, index):
		if index < 0:
			return
		note = self.widget_notes.itemData(index)
		if not note:
			if index >= len(self.notes_current_list):
				return
			note = self.notes_current_list[index]
		note_html = note.get("body")
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		if self.notes_force_reload or not note_html:
			note_html = self._read_note_html(folder, title)
			if note_html is None:
				note_html = ""
			if self.notes_require_match_on_show and not note_html:
				self.notes_require_match_on_show = False
				self._prompt_notes_reselect(folder, title)
				return
			note["body"] = note_html
		note_key = f"{folder}/{title}"
		if self.notes_force_reload:
			note_md = notes_html_to_markdown(note_html, cache_key=note_key, force_html=True)
			delete_cache_file(note_key)
			self.notes_force_reload = False
		else:
			note_md = notes_html_to_markdown(note_html, cache_key=note_key)
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
				self.topleft.setHtml("")
				self.topright.clear()
				self._set_notes_dirty(False)
				return
		self._request_async_preview_render(note_md, debounce_ms=0)
		self._set_notes_dirty(False)

	def save_notes_sync(self):
		if not self.notes_active:
			return
		current_index = self.widget_notes.currentIndex()
		if current_index < 0:
			return
		note = self.widget_notes.itemData(current_index)
		if not note:
			if current_index >= len(self.notes_current_list):
				return
			note = self.notes_current_list[current_index]
		folder = (note.get("folder") or "Unfiled").strip() or "Unfiled"
		title = note.get("title") or "(Untitled)"
		# 保存前检查笔记路径是否仍然有效
		check_html = self._read_note_html(folder, title)
		if check_html is None or not check_html.strip():
			# 路径不存在，锁定编辑器并提示用户重新选择
			self._set_notes_active(False)
			self._prompt_notes_reselect(folder, title)
			return
		note_md = self.bottom.toPlainText()
		new_title = self._notes_title_from_md(note_md)
		if new_title and new_title != title:
			if not self._confirm_notes_title_change(title, new_title):
				self._set_notes_dirty(True)
				return
		note_html = markdown_to_html(note_md)
		note_html = embed_markdown(note_html, note_md)
		try:
			self._write_note_html(folder, title, note_html)
		except Exception:
			# 写入失败，可能是路径不存在，锁定编辑器并提示用户
			self._set_notes_active(False)
			self._prompt_notes_reselect(folder, title)
			return
		note_key = f"{folder}/{title}"
		delete_cache_file(note_key)
		note["body"] = note_html
		final_title = new_title if (new_title and new_title != title) else title
		final_note_key = f"{folder}/{final_title}"
		self._backup_notes_mode_if_changed(final_note_key, final_title, note_md)
		if new_title and new_title != title:
			note["title"] = new_title
			self.notes_current_title = new_title
			self.notes_pending_title = new_title
			self.notes_pending_folder = folder
			self._start_notes_wait(folder, new_title)
		try:
			_write_notes_cache(self.notes_data, self.notes_cache_path)
		except Exception:
			pass
		self._set_notes_dirty(False)

	def _write_note_html(self, folder, title, html):
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
				set targetNote to missing value
				repeat with n in notes
					set t to name of n
					if t is equal to targetTitle then
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
						if f is equal to targetFolder then
							set targetNote to n
							exit repeat
						end if
					end if
				end repeat
				if targetNote is missing value then error "NOT_FOUND"
				set body of targetNote to newHTML
			end tell
		end run
		'''
		subprocess.check_call(["osascript", "-e", script, folder, title, path])

	def export_file(self):
		home_dir = str(Path.home())
		fj = QFileDialog.getExistingDirectory(self, 'Open', home_dir)
		if fj != '':
			text_1 = self.bottom.toPlainText()
			tarname = self.widget0.currentText() + ".md"
			fulldir = os.path.join(fj, tarname)
			with open(fulldir, 'w', encoding='utf-8') as f1:
				f1.write(text_1)

			text_2 = self.bottom.toPlainText()
			endbio = self.addb2(text_2.replace('*', ''))
			tarname2 = self.widget0.currentText() + "_bionic.md"
			fulldirw = os.path.join(fj, tarname2)
			with open(fulldirw, 'w', encoding='utf-8') as f1:
				f1.write(endbio)

	def clear_all(self):
		self._set_notes_active(False)
		w3.widget0.currentIndexChanged.disconnect(w3.index_change)
		w3.bottom.textChanged.disconnect(w3.text_change)

		self.bottom.clear()
		self.topleft.setHtml("")
		self.topright.clear()

		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
		fj = QFileDialog.getOpenFileName(self, "Open File", home_dir, "Markdown Files (*.md)")
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
			ResultEnd = 'The clipboard is empty.'
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
			ResultEnd = 'The clipboard is empty.'
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
			ResultEnd = 'The clipboard is empty.'
			ResultEnd = ResultEnd.encode('utf-8').decode('utf-8', 'ignore')
			uid = os.getuid()
			env = os.environ.copy()
			env['__CF_USER_TEXT_ENCODING'] = f'{uid}:0x8000100:0x8000100'
			p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, env=env)
			p.communicate(input=ResultEnd.encode('utf-8'))

	def md2html(self, mdstr, pre_rendered_html=None):
		extras = ['code-friendly', 'fenced-code-blocks', 'footnotes', 'tables', 'code-color', 'pyshell', 'nofollow',
				  'cuddled-lists', 'header ids', 'strike', 'nofollow']

		html = """
		<html>
		<head>
		<meta content="text/html; charset=utf-8" http-equiv="content-type" />
		<style>
				.hll { background-color: #ffffcc }
				.c { color: #0099FF; font-style: italic } /* Comment */
				.err { color: #AA0000; background-color: #FFAAAA } /* Error */
				.k { color: #006699; font-weight: bold } /* Keyword */
				.o { color: #555555 } /* Operator */
				.ch { color: #0099FF; font-style: italic } /* Comment.Hashbang */
				.cm { color: #0099FF; font-style: italic } /* Comment.Multiline */
				.cp { color: #009999 } /* Comment.Preproc */
				.cpf { color: #0099FF; font-style: italic } /* Comment.PreprocFile */
				.c1 { color: #0099FF; font-style: italic } /* Comment.Single */
				.cs { color: #0099FF; font-weight: bold; font-style: italic } /* Comment.Special */
				.gd { background-color: #FFCCCC; border: 1px solid #CC0000 } /* Generic.Deleted */
				.ge { font-style: italic } /* Generic.Emph */
				.gr { color: #FF0000 } /* Generic.Error */
				.gh { color: #003300; font-weight: bold } /* Generic.Heading */
				.gi { background-color: #CCFFCC; border: 1px solid #00CC00 } /* Generic.Inserted */
				.go { color: #AAAAAA } /* Generic.Output */
				.gp { color: #000099; font-weight: bold } /* Generic.Prompt */
				.gs { font-weight: bold } /* Generic.Strong */
				.gu { color: #003300; font-weight: bold } /* Generic.Subheading */
				.gt { color: #99CC66 } /* Generic.Traceback */
				.kc { color: #006699; font-weight: bold } /* Keyword.Constant */
				.kd { color: #006699; font-weight: bold } /* Keyword.Declaration */
				.kn { color: #006699; font-weight: bold } /* Keyword.Namespace */
				.kp { color: #006699 } /* Keyword.Pseudo */
				.kr { color: #006699; font-weight: bold } /* Keyword.Reserved */
				.kt { color: #007788; font-weight: bold } /* Keyword.Type */
				.m { color: #FF6600 } /* Literal.Number */
				.s { color: #CC3300 } /* Literal.String */
				.na { color: #330099 } /* Name.Attribute */
				.nb { color: #336666 } /* Name.Builtin */
				.nc { color: #00AA88; font-weight: bold } /* Name.Class */
				.no { color: #336600 } /* Name.Constant */
				.nd { color: #9999FF } /* Name.Decorator */
				.ni { color: #999999; font-weight: bold } /* Name.Entity */
				.ne { color: #CC0000; font-weight: bold } /* Name.Exception */
				.nf { color: #CC00FF } /* Name.Function */
				.nl { color: #9999FF } /* Name.Label */
				.nn { color: #00CCFF; font-weight: bold } /* Name.Namespace */
				.nt { color: #330099; font-weight: bold } /* Name.Tag */
				.nv { color: #003333 } /* Name.Variable */
				.ow { color: #000000; font-weight: bold } /* Operator.Word */
				.w { color: #bbbbbb } /* Text.Whitespace */
				.mb { color: #FF6600 } /* Literal.Number.Bin */
				.mf { color: #FF6600 } /* Literal.Number.Float */
				.mh { color: #FF6600 } /* Literal.Number.Hex */
				.mi { color: #FF6600 } /* Literal.Number.Integer */
				.mo { color: #FF6600 } /* Literal.Number.Oct */
				.sa { color: #CC3300 } /* Literal.String.Affix */
				.sb { color: #CC3300 } /* Literal.String.Backtick */
				.sc { color: #CC3300 } /* Literal.String.Char */
				.dl { color: #CC3300 } /* Literal.String.Delimiter */
				.sd { color: #CC3300; font-style: italic } /* Literal.String.Doc */
				.s2 { color: #CC3300 } /* Literal.String.Double */
				.se { color: #CC3300; font-weight: bold } /* Literal.String.Escape */
				.sh { color: #CC3300 } /* Literal.String.Heredoc */
				.si { color: #AA0000 } /* Literal.String.Interpol */
				.sx { color: #CC3300 } /* Literal.String.Other */
				.sr { color: #33AAAA } /* Literal.String.Regex */
				.s1 { color: #CC3300 } /* Literal.String.Single */
				.ss { color: #FFCC33 } /* Literal.String.Symbol */
				.bp { color: #336666 } /* Name.Builtin.Pseudo */
				.fm { color: #CC00FF } /* Name.Function.Magic */
				.vc { color: #003333 } /* Name.Variable.Class */
				.vg { color: #003333 } /* Name.Variable.Global */
				.vi { color: #003333 } /* Name.Variable.Instance */
				.vm { color: #003333 } /* Name.Variable.Magic */
				.il { color: #FF6600 } /* Literal.Number.Integer.Long */
				table {
						  font-family: verdana,arial,sans-serif;
						  font-size:11px;
						  color:#333333;
						  border-width: 1px;
						  border-color: #999999;
						  border-collapse: collapse;
						  }
				th {
					 background:#b5cfd2 url('cell-blue.jpg');
					 border-width: 1px;
					 padding: 8px;
					 border-style: solid;
					 border-color: #999999;
					 }
				td {
					 background:#dcddc0 url('cell-grey.jpg');
					 border-width: 1px;
					 padding: 8px;
					 border-style: solid;
					 border-color: #999999;
					 }
		</style>
		</head>
		<body>
				%s
		</body>
		</html>
		"""
		if pre_rendered_html is None:
			clean_one = mdstr.replace('\\(', '$').replace('\\)', '$').replace('\\[', '$').replace('\\]', '$')
			clean_two = re.sub(
				r'\$(.*?)\$',
				lambda m: '$' + re.sub(r'[\n\t ]+', '', m.group(1)) + '$',
				clean_one,
				flags=re.DOTALL,
			)
			clean_three = re.sub(r'\|(\n(\t)*\n(\t)*)\|', '|\n|', clean_two)
			ret = markdown2.markdown(clean_three, extras=extras)
		else:
			ret = pre_rendered_html
		middlehtml = html % ret
		font_family = getattr(self, "_current_font_family", None) or self._resolve_font_family()
		font_size = getattr(self, "_current_font_size", None) or self._read_font_size()
		bg_color = getattr(self, "_current_bg_color", "#FFFFFF")
		text_color = '#FFFFFF' if is_dark_theme(app) else '#000000'
		html_content = """
		<!DOCTYPE html>
		<html lang="en">
		<head>
				<style>
					 html, body {
						  margin: 0;
						  font-size: %dpx;
						  font-family: "%s";
						  padding: 0;
						  background-color: %s;
						  color: %s;
					 }
					 table, th, td {
						  color: %s !important;
					 }
				</style>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<script
					 src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_CHTML">
				</script>
		</head>
		<body>
				%s
				<script type='text/x-mathjax-config'>
				MathJax.Hub.Config({
					 displayAlign: 'left',
					 displayIndent: '4em',
					 tex2jax: {
						  inlineMath: [['$','$'], ['\\\\(','\\\\)']],
						  displayMath: [['$$','$$'], ['\\[','\\]']]
					 },
					 TeX:{
						  equationNumbers:{
								autoNumber:"AMS"
						  }
					 }
				});
				</script>
		</body>
		</html>
		""" % (font_size, font_family, bg_color, text_color, text_color, middlehtml)
		if getattr(self, '_teleprompter_mode', False):
			html_content = html_content.replace(
				'</head>',
				'<style>body { line-height: 2.0 !important; }</style>\n</head>'
			)
		return html_content

	def _start_update_check_worker(self):
		if self.update_check_worker is not None and self.update_check_worker.isRunning():
			return
		self.update_check_worker = UpdateCheckWorker(
			current_version='v' + VERSION,
			interval_seconds=86400,
			parent=self
		)
		self.update_check_worker.update_available.connect(self.on_update_available)
		self.update_check_worker.checked_ok.connect(self.on_update_checked_ok)
		self.update_check_worker.checked_error.connect(self.on_update_checked_error)
		self.update_check_worker.start()

	def _stop_update_check_worker(self):
		worker = self.update_check_worker
		if worker is None:
			return
		if worker.isRunning():
			worker.stop()
			worker.wait(3000)
		try:
			worker.deleteLater()
		except Exception:
			pass
		self.update_check_worker = None

	def set_auto_update_check_enabled(self, enabled):
		enabled = bool(enabled)
		self.auto_update_check_enabled = enabled
		save_auto_update_check_enabled(enabled)
		if 'auto_update_check_action' in globals():
			try:
				auto_update_check_action.blockSignals(True)
				auto_update_check_action.setChecked(enabled)
				auto_update_check_action.blockSignals(False)
			except Exception:
				pass
		if enabled:
			self._start_update_check_worker()
		else:
			self._stop_update_check_worker()

	def _start_auto_update_check_after_startup(self):
		if not self.auto_update_check_enabled:
			return
		self._start_update_check_worker()

	def set_update_alert_dedupe_enabled(self, enabled):
		enabled = bool(enabled)
		self.update_alert_dedupe_enabled = enabled
		save_update_alert_dedupe_enabled(enabled)
		if not enabled:
			self._last_notified_update_version = None
		if 'update_alert_dedupe_action' in globals():
			try:
				update_alert_dedupe_action.blockSignals(True)
				update_alert_dedupe_action.setChecked(enabled)
				update_alert_dedupe_action.blockSignals(False)
			except Exception:
				pass
	
	@pyqtSlot(str)
	def on_update_available(self, latest: str):
		if not latest:
			return
		if self._update_notice_box is not None:
			try:
				if self._update_notice_box.isVisible():
					self._update_notice_box.raise_()
					self._update_notice_box.activateWindow()
					return
				self._update_notice_box.close()
			except Exception:
				pass
			self._update_notice_box = None
		if self.update_alert_dedupe_enabled and self._last_notified_update_version == latest:
			return
		if self.update_alert_dedupe_enabled:
			self._last_notified_update_version = latest
		msg = CustomMessageBox(
			self.tr(f"New version %n is available. Open release note page?").replace('%n', latest),
			parent=self,
			buttons=(self.tr("Open"), self.tr("Later"))
		)
		msg.setWindowTitle(self.tr("Update Available"))
		msg.setWindowModality(Qt.WindowModality.NonModal)
		msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
		if msg.btns:
			msg.btns[0].clicked.connect(lambda: webbrowser.open('https://github.com/Ryan-the-hito/Watermelon/releases'))
		msg.destroyed.connect(self._on_update_notice_destroyed)
		self._update_notice_box = msg
		msg.show()
		msg.raise_()
		msg.activateWindow()

	# 或者你也可以这样：仅在有更新时展示现有的 WindowUpdate 小窗
	# self.win_update.show()  # 它会 show() 并 checkupdate()，但建议只 show，然后把 latest 显示出来

	@pyqtSlot(str)
	def on_update_checked_ok(self, latest: str):
		# 可选：比如在日志里记录或更新某个状态标签（主线程里的标签）
		# print(f"Checked latest: {latest}")
		pass

	@pyqtSlot(str)
	def on_update_checked_error(self, err: str):
		# 可选：记录错误，不弹框打扰用户
		# print(f"Check update error: {err}")
		pass

	def _on_update_notice_destroyed(self, _obj=None):
		self._update_notice_box = None

class window4(QWidget):  # Customization settings
	def __init__(self):
		super().__init__()
		self.radius = 16  # 圆角半径，可按 macOS 15 或 26 设置为 16~26

		self.setWindowFlags(
			Qt.WindowType.FramelessWindowHint |
			Qt.WindowType.Window |
			Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

		self.init_ui()

	def init_ui(self):
		self.setUpMainWindow()
		self.setFixedSize(640, 550)
		self.center()
		self.setFocus()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

		rect = QRectF(self.rect())
		path = QPainterPath()
		path.addRoundedRect(rect, self.radius, self.radius)

		painter.setClipPath(path)
		bg_color = self.palette().color(QPalette.ColorRole.Window)
		painter.fillPath(path, bg_color)

	# 让无边框窗口可拖动
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.drag_pos)
			event.accept()
	# def __init__(self):
	# 	super().__init__()
	# 	self.initUI()

	# def initUI(self):  # 设置窗口内布局
	# 	self.setUpMainWindow()
	# 	self.resize(640, 400)
	# 	self.center()
	# 	self.setWindowTitle('Customization settings')
	# 	self.setFocus()
	# 	self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		# 添加关闭按钮（仿 macOS 左上角红色圆点）
		# self.close_button = QPushButton(self)
		# self.close_button.setFixedSize(12, 12)
		# self.close_button.move(10, 10)
		# self.close_button.setStyleSheet("""
		#			 QPushButton {
		#				 background-color: #FF5F57;
		#				 border-radius: 6px;
		#				 border: none;
		#			 }
		#			 QPushButton:hover {
		#				 background-color: #BF4943;
		#			 }
		#		 """)
		# self.close_button.clicked.connect(self.close)
		self.close_button = MacWindowButton("#FF605C", "x", self)
		self.close_button.move(10, 10)
		self.close_button.clicked.connect(self.close)

		wid0 = QWidget()
		lbl0 = QLabel("<h2>Manage recent files</h2>", self)
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
		self.text_feed.setFixedHeight(340)
		self.text_feed.itemSelectionChanged.connect(self.item_click)
		b41 = QHBoxLayout()
		b41.setContentsMargins(0, 0, 0, 0)
		b41.addWidget(self.text_feed)
		wid1.setLayout(b41)

		wid11 = QWidget()
		self.btn4_1 = WhiteButton('Delete', self)
		# self.btn4_1.setFixedHeight(20)
		self.btn4_1.setFixedWidth(250)
		self.btn4_1.setVisible(False)
		self.btn4_1.clicked.connect(self.delete_item)
		btn4_11 = WhiteButton('Save', self)
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

		self.checkBox0 = QCheckBox('Automatically scroll simultaneously', self)
		self.checkBox0.setChecked(True)
		self.checkBox0.clicked.connect(self.auto_scroll)

		self.checkBox_top = QCheckBox('Always on top', self)
		self.checkBox_top.setChecked(w3.is_always_on_top())
		self.checkBox_top.clicked.connect(self.toggle_on_top)

		self.checkBox_eye_care = QCheckBox('Eye care mode', self)
		# 读取用户偏好设置（默认是白色，勾选变护眼色）
		bg_pref_file = BasePath + 'bg_color.txt'
		if os.path.exists(bg_pref_file):
			bg_pref = codecs.open(bg_pref_file, 'r', encoding='utf-8').read().strip()
			self.checkBox_eye_care.setChecked(bg_pref == 'cream')
		else:
			self.checkBox_eye_care.setChecked(False)
		self.checkBox_eye_care.clicked.connect(self.toggle_bg_color)

		self.widget1 = QComboBox(self)
		self.widget1.addItems(['Last used', 'Default font'])
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

		lbl1 = QLabel("Font size: ", self)
		sld = QSlider(Qt.Orientation.Horizontal, self)
		sld.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		sld.setRange(14, 50)
		dfontsize = int(codecs.open(BasePath + 'fs.txt', 'r', encoding='utf-8').read())
		sld.setValue(dfontsize)
		font_family = codecs.open(BasePath + 'lastused.txt', 'r', encoding='utf-8').read()
		if font_family == '0':
			font_path = BasePath + "chillduanheisong_widelight.otf"  # 替换为你自己的字体文件路径
			font_family = self.load_font(font_path)
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
		main_h_box.addWidget(wid2)
		# main_h_box.addStretch()
		self.setLayout(main_h_box)

		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
			raise Exception("Font failed to load! Check the font path.")
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
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
			w3.topleft.setHtml(endhtml)
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
			w3.topleft.setHtml(endhtml)
			endbio = w3.addb2(previewtext.replace('*', ''))
			endhtmlbio = w3.md2html(endbio)
			w3.topright.setHtml(endhtmlbio)
			w3.bottom.textChanged.connect(w3.text_change)
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
		with open(BasePath + 'bg_color.txt', 'w', encoding='utf-8') as f0:
			f0.write(pref)
		# 更新w3中的组件背景颜色
		w3.set_bg_color(bg_color)

	def value_change(self, value):
		self.lbl2.setText(str(value))
		self.lbl2.adjustSize()
		targetfont = self.widget1.currentText()
		if targetfont == 'Last used':
			targetfont = codecs.open(BasePath + 'lastused.txt', 'r', encoding='utf-8').read()
			if targetfont == '0':
				font_path = BasePath + "chillduanheisong_widelight.otf"  # 替换为你自己的字体文件路径
				targetfont = self.load_font(font_path)
		if targetfont == 'Default font':
			font_path = BasePath + "chillduanheisong_widelight.otf"  # 替换为你自己的字体文件路径
			targetfont = self.load_font(font_path)
		w3.set_textedit_font(value, targetfont)
		with open(BasePath + 'fs.txt', 'w', encoding='utf-8') as f0:
			f0.write(str(value))

	def font_change(self, i):
		if i == 0:
			targetsize = int(self.lbl2.text())
			targetfont = codecs.open(BasePath + 'lastused.txt', 'r', encoding='utf-8').read()
			if targetfont == '0':
				font_path = BasePath + "chillduanheisong_widelight.otf"  # 替换为你自己的字体文件路径
				targetfont = self.load_font(font_path)
			w3.set_textedit_font(targetsize, targetfont)
		if i == 1:
			targetsize = int(self.lbl2.text())
			font_path = BasePath + "chillduanheisong_widelight.otf"  # 替换为你自己的字体文件路径
			targetfont = self.load_font(font_path)
			w3.set_textedit_font(targetsize, targetfont)
			with open(BasePath + 'lastused.txt', 'w', encoding='utf-8') as f0:
				f0.write('0')
		if i != 0 and i != 1:
			targetsize = int(self.lbl2.text())
			targetfont = self.widget1.itemText(i)
			w3.set_textedit_font(targetsize, targetfont)
			with open(BasePath + 'lastused.txt', 'w', encoding='utf-8') as f0:
				f0.write(targetfont)

	def activate(self):  # 设置窗口显示
		self.show()
		self.btn4_1.setVisible(False)
		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
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
		border-radius:4px;
		border: 1px solid gray;
		background-color: #FFFFFF;
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
        border: 1px solid grey;
        border-radius:4px;
        padding: 1px 5px 1px 3px;
        background-clip: border;
        background-color: #FFFFFF;
        color: #000000;
        font: 14pt Times New Roman;
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
		border-radius:4px;
		border: 1px solid gray;
		background-color: #3A3A3A;
		color: #FFFFFF;
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
		border: 1px solid grey;
		border-radius:4px;
		padding: 1px 5px 1px 3px;
		background-clip: border;
		background-color: #3A3A3A;
		color: #FFFFFF;
		font: 14pt Times New Roman;
}
	QLabel{
		color: #FFFFFF;
}
'''


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
	action8.triggered.connect(w3.assigntoall)
	btna4.triggered.connect(w3.pin_a_tab)
	teleprompter_action.triggered.connect(w3.toggle_teleprompter)
	open_backup_folder_action.triggered.connect(w3.open_current_backup_folder)
	w3.btn0_1.clicked.connect(w4.activate)
	w3.btn0_2.clicked.connect(w3.toggle_notes_mode)
	w3.set_textedit_font(w3._current_font_size, w3._current_font_family)
	apply_bg_color_from_pref(w3)
	app.exec()
