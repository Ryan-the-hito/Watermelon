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
							 QSystemTrayIcon, QMenu, QComboBox, QDialog,
							 QMenuBar, QFileDialog, QMessageBox, QLineEdit,
							 QSplitter, QTextEdit, QListWidget, QCheckBox, QSlider,
							 QFrame)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QColor, QFontDatabase, QPixmap, QCursor, QGuiApplication
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
import os
from pathlib import Path
import markdown2
from datetime import datetime
import matplotlib.font_manager
from PIL import Image, ImageQt
import time
try:
	from AppKit import NSWorkspace
except ImportError:
	NSWorkspace = None

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Watermelon.app/Contents/Resources/'
#BasePath = ''
NOTES_CACHE_PATH = os.path.join(BasePath, "notes_cache.json")
DEBUG_LAYOUT = False

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

action6 = QAction("⚙️ Settings")
menu.addAction(action6)

menu.addSeparator()

action5 = QAction("🆕 Check for Updates")
menu.addAction(action5)

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


class window_about(QWidget):  # 增加说明页面(About)
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):  # 说明页面内信息
		self.setUpMainWindow()
		self.resize(400, 410)
		self.center()
		self.setWindowTitle('About')
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widg1 = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wtmenu.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
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
		lbl0 = QLabel('Watermelon', self)
		font = PyQt6.QtGui.QFont()
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
		lbl1 = QLabel('Version 2.2.1', self)
		blay3 = QHBoxLayout()
		blay3.setContentsMargins(0, 0, 0, 0)
		blay3.addStretch()
		blay3.addWidget(lbl1)
		blay3.addStretch()
		widg3.setLayout(blay3)

		widg4 = QWidget()
		lbl2 = QLabel('Thanks for your love🤟.', self)
		blay4 = QHBoxLayout()
		blay4.setContentsMargins(0, 0, 0, 0)
		blay4.addStretch()
		blay4.addWidget(lbl2)
		blay4.addStretch()
		widg4.setLayout(blay4)

		widg5 = QWidget()
		lbl3 = QLabel('感谢您的喜爱！', self)
		blay5 = QHBoxLayout()
		blay5.setContentsMargins(0, 0, 0, 0)
		blay5.addStretch()
		blay5.addWidget(lbl3)
		blay5.addStretch()
		widg5.setLayout(blay5)

		widg6 = QWidget()
		lbl4 = QLabel('♥‿♥', self)
		blay6 = QHBoxLayout()
		blay6.setContentsMargins(0, 0, 0, 0)
		blay6.addStretch()
		blay6.addWidget(lbl4)
		blay6.addStretch()
		widg6.setLayout(blay6)

		widg7 = QWidget()
		lbl5 = QLabel('※\(^o^)/※', self)
		blay7 = QHBoxLayout()
		blay7.setContentsMargins(0, 0, 0, 0)
		blay7.addStretch()
		blay7.addWidget(lbl5)
		blay7.addStretch()
		widg7.setLayout(blay7)

		widg8 = QWidget()
		bt1 = QPushButton('The Author', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.intro)
		bt2 = QPushButton('Github Page', self)
		bt2.setMaximumHeight(20)
		bt2.setMinimumWidth(100)
		bt2.clicked.connect(self.homepage)
		blay8 = QHBoxLayout()
		blay8.setContentsMargins(0, 0, 0, 0)
		blay8.addStretch()
		blay8.addWidget(bt1)
		blay8.addWidget(bt2)
		blay8.addStretch()
		widg8.setLayout(blay8)

		bt7 = QPushButton('Buy me a cup of coffee☕', self)
		bt7.setMaximumHeight(20)
		bt7.setMinimumWidth(215)
		bt7.clicked.connect(self.coffee)

		widg8_5 = QWidget()
		blay8_5 = QHBoxLayout()
		blay8_5.setContentsMargins(0, 0, 0, 0)
		blay8_5.addStretch()
		blay8_5.addWidget(bt7)
		blay8_5.addStretch()
		widg8_5.setLayout(blay8_5)

		widg9 = QWidget()
		bt3 = QPushButton('🍪\n¥5', self)
		bt3.setMaximumHeight(50)
		bt3.setMinimumHeight(50)
		bt3.setMinimumWidth(50)
		bt3.clicked.connect(self.donate)
		bt4 = QPushButton('🥪\n¥10', self)
		bt4.setMaximumHeight(50)
		bt4.setMinimumHeight(50)
		bt4.setMinimumWidth(50)
		bt4.clicked.connect(self.donate2)
		bt5 = QPushButton('🍜\n¥20', self)
		bt5.setMaximumHeight(50)
		bt5.setMinimumHeight(50)
		bt5.setMinimumWidth(50)
		bt5.clicked.connect(self.donate3)
		bt6 = QPushButton('🍕\n¥50', self)
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
		lbl6 = QLabel('© 2022 Ryan-the-hito. All rights reserved.', self)
		blay10 = QHBoxLayout()
		blay10.setContentsMargins(0, 0, 0, 0)
		blay10.addStretch()
		blay10.addWidget(lbl6)
		blay10.addStretch()
		widg10.setLayout(blay10)

		main_h_box = QVBoxLayout()
		main_h_box.addWidget(widg1)
		main_h_box.addWidget(widg2)
		main_h_box.addWidget(widg3)
		main_h_box.addWidget(widg4)
		main_h_box.addWidget(widg5)
		main_h_box.addWidget(widg6)
		main_h_box.addWidget(widg7)
		main_h_box.addWidget(widg8)
		main_h_box.addWidget(widg8_5)
		main_h_box.addWidget(widg9)
		main_h_box.addWidget(widg10)
		main_h_box.addStretch()
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
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay5.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
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
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay10.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
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
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay20.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
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
		self.setWindowTitle("Thank you for your support!")
		self.center()
		self.resize(400, 390)
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		widge_all = QWidget()
		l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'wechat50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l1.setMaximumSize(160, 240)
		l1.setScaledContents(True)
		l2 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(BasePath + 'alipay50.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
		l2.setMaximumSize(160, 240)
		l2.setScaledContents(True)
		bk = QHBoxLayout()
		bk.setContentsMargins(0, 0, 0, 0)
		bk.addWidget(l1)
		bk.addWidget(l2)
		widge_all.setLayout(bk)

		m1 = QLabel('Thank you for your kind support! 😊', self)
		m2 = QLabel('I will write more interesting apps! 🥳', self)

		widg_c = QWidget()
		bt1 = QPushButton('Thank you!', self)
		bt1.setMaximumHeight(20)
		bt1.setMinimumWidth(100)
		bt1.clicked.connect(self.cancel)
		bt2 = QPushButton('Neither one above? Buy me a coffee~', self)
		bt2.setMaximumHeight(20)
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


class window_update(QWidget):  # 增加更新页面（Check for Updates）
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):  # 说明页面内信息

		self.lbl = QLabel('Current Version: v2.2.1', self)
		self.lbl.move(30, 45)

		lbl0 = QLabel('Download Update:', self)
		lbl0.move(30, 75)

		lbl1 = QLabel('Latest Version:', self)
		lbl1.move(30, 15)

		self.lbl2 = QLabel('', self)
		self.lbl2.move(122, 15)

		bt1 = QPushButton('GitHub', self)
		bt1.setFixedWidth(120)
		bt1.clicked.connect(self.upd)
		bt1.move(150, 75)

		bt2 = QPushButton('Baidu Netdisk', self)
		bt2.setFixedWidth(120)
		bt2.clicked.connect(self.upd2)
		bt2.move(150, 105)

		self.resize(300, 150)
		self.center()
		self.setWindowTitle('Watermelon Updates')
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def upd(self):
		webbrowser.open('https://github.com/Ryan-the-hito/Watermelon/releases')

	def upd2(self):
		webbrowser.open('https://pan.baidu.com/s/1O3YElKc8vn9-4lsnM7QShA?pwd=erq7')

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
			nowversion = self.lbl.text().replace('Current Version: ', '')
			if result == nowversion:
				alertupdate = result + '. You are up to date!'
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
			else:
				alertupdate = result + ' is ready!'
				self.lbl2.setText(alertupdate)
				self.lbl2.adjustSize()
		except:
			alertupdate = 'No Intrenet'
			self.lbl2.setText(alertupdate)
			self.lbl2.adjustSize()

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


class NotesFolderDialog(QDialog):
	note_selected = pyqtSignal(object)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Select Notes")
		self.center()
		self.resize(520, 320)
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		# self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
		# self._centered_once = False

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

		select_btn = QPushButton("Select")
		select_btn.setFixedSize(100, 20)
		select_btn.clicked.connect(self.select_current)
		cancel_btn = QPushButton("Cancel")
		cancel_btn.setFixedSize(100, 20)
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
		w3.setObjectName("Main")

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(w3)
		# layout.addWidget(self.search_input)
		# layout.addWidget(splitter)
		# layout.addLayout(btn_row)
		self.setLayout(layout)

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
			self.set_status("Select a note.")
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
		self.move(500, 300)


class window3(QWidget):  # 主窗口
	def __init__(self):
		super().__init__()
		self._splitter2_ratio = None
		self._splitter2_user_set = False
		self._always_on_top = True
		self._screen_signals_connected = False
		self._tracked_screen = None
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
		self.notes_last_folder = None
		self.notes_last_title = None
		self.notes_refresh_in_progress = False
		self._notes_positions = {}
		self.notes_wait_dialog = None
		self.notes_wait_timer = None
		self.notes_wait_target = None
		self.notes_wait_start = None
		self.notes_cache_worker = NotesCacheWorker(self.notes_cache_path, self)
		self.notes_cache_worker.start()

		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)

		self._current_font_size = self._read_font_size()
		self._current_font_family = self._resolve_font_family()
		self.set_textedit_font(self._current_font_size, self._current_font_family)

		self.topleft = QWebEngineView(self)
		self.topleft.setStyleSheet("border: 0px; background: #F3F2EE;")
		self.topleft.page().setBackgroundColor(QColor("#F3F2EE"))
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
		self.scrollbar = self.bottom.verticalScrollBar()
		self.scrollbar.valueChanged.connect(self.scrollchanged)
		self.bottom.cursorPositionChanged.connect(self.cursorchanged)

		self.splitter1 = QSplitter(Qt.Orientation.Horizontal)
		self.splitter1.addWidget(self.topleft_frame)
		self.splitter1.addWidget(self.topright)
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

		self.btn_sub1 = QPushButton('Open', self)
		self.btn_sub1.clicked.connect(self.open_file)
		self.btn_sub1.setFixedSize(230, 20)
		self.btn_sub2 = QPushButton('New', self)
		self.btn_sub2.clicked.connect(self.new_file)
		self.btn_sub2.setFixedSize(230, 20)

		self.widget0 = QComboBox(self)
		self.widget0.setCurrentIndex(0)

		self.widget0.setFixedWidth(230)
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

		self.btn_notes_folder = QPushButton('Notes Folder', self)
		self.btn_notes_folder.clicked.connect(self.open_notes_folder_dialog)
		self.btn_notes_folder.setFixedSize(230, 20)

		self.widget_notes = QComboBox(self)
		self.widget_notes.setFixedWidth(230)
		self.widget_notes.setEnabled(False)
		self.widget_notes.currentIndexChanged.connect(self.notes_index_change)

		self.btn_notes_save = QPushButton('Save', self)
		self.btn_notes_save.clicked.connect(self.save_notes_sync)
		self.btn_notes_save.setFixedSize(230, 20)
		self.btn_notes_save.setEnabled(False)
		self.btn_notes_save.setStyleSheet('''
				QPushButton:disabled{
				border: 1px solid #999999;
				background-color: #E6E6E6;
				border-radius: 4px;
				padding: 1px;
				color: #777777
				}
				''')

		self.btn_notes_new = QPushButton('New', self)
		self.btn_notes_new.clicked.connect(self.new_notes_note)
		self.btn_notes_new.setFixedSize(230, 20)
		self.btn_notes_new.setEnabled(False)
		self.btn_notes_new.setStyleSheet('''
				QPushButton:disabled{
				border: 1px solid #999999;
				background-color: #E6E6E6;
				border-radius: 4px;
				padding: 1px;
				color: #777777
				}
				''')

		self.btn_notes_export = QPushButton('Export', self)
		self.btn_notes_export.clicked.connect(self.export_notes_file)
		self.btn_notes_export.setFixedSize(230, 20)
		self.btn_notes_export.setEnabled(False)
		self.btn_notes_export.setStyleSheet('''
				QPushButton:disabled{
				border: 1px solid #999999;
				background-color: #E6E6E6;
				border-radius: 4px;
				padding: 1px;
				color: #777777
				}
				''')

		self.btn_sub3 = QPushButton('Export', self)
		self.btn_sub3.clicked.connect(self.export_file)
		self.btn_sub3.setFixedSize(230, 20)

		self.btn_sub4 = QPushButton('Clear', self)
		self.btn_sub4.clicked.connect(self.clear_all)
		self.btn_sub4.setFixedSize(230, 20)

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

		self.btn_00 = QPushButton('', self)
		self.btn_00.clicked.connect(self.pin_a_tab)
		self.btn_00.setFixedHeight(10)
		self.btn_00.setFixedWidth(1200)
		self.btn_00.setStyleSheet('''
				border: 1px outset grey;
				background-color: #0085FF;
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF''')
		self.btn_00.move(160, SCREEN_HEIGHT - 35)

		self.btn0_1 = QPushButton('', self)
		self.btn0_1.setFixedSize(25, 25)
		self.btn0_1.setStyleSheet('''
				QPushButton{
				border: transparent;
				background-color: transparent;
				border-image: url(/Applications/Watermelon.app/Contents/Resources/set2.png);
				}
				QPushButton:pressed{
				border: 1px outset grey;
				background-color: #0085FF;
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF
				}
				''')
		self.btn0_1.move(35, SCREEN_HEIGHT - 185)

		self.btn0_2 = QPushButton('', self)
		self.btn0_2.setFixedSize(25, 25)
		self.btn0_2.setStyleSheet('''
				QPushButton{
				border: transparent;
				background-color: transparent;
				border-image: url(/Applications/Watermelon.app/Contents/Resources/repeat.png);
				}
				QPushButton:pressed{
				border: 1px outset grey;
				background-color: #0085FF;
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF
				}
				''')
		self.btn0_2.move(1435, SCREEN_HEIGHT - 182)

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
		endhtml = self.md2html(previewtext)
		self.topleft.setHtml(endhtml)
		endbio = self.addb2(previewtext.replace('*', ''))
		endhtmlbio = self.md2html(endbio)
		self.topright.setHtml(endhtmlbio)
		self.widget0.currentIndexChanged.connect(self.index_change)

		w2.setStyleSheet(style_sheet_ori)

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
		self.btn0_2.raise_()

		self.assigntoall()

		w2.checkupdate()
		if w2.lbl2.text() != 'No Intrenet' and 'ready' in w2.lbl2.text():
			w2.show()

	def showEvent(self, event):
		super().showEvent(event)
		self._connect_screen_signals()

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
		self.btn_00.move(160, screen_height - 35)
		# 调整设置按钮的位置
		self.btn0_1.move(35, screen_height - 185)
		self.btn0_2.move(1435, screen_height - 182)

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
		self.show()
		if self.i % 2 == 1:  # show
			btna4.setChecked(True)
			self.btn_00.setFixedHeight(10)
			self.btn_00.setFixedWidth(1200)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #0085FF;
						border-radius: 4px;
						padding: 1px;
						color: #FFFFFF''')
			self.btn_00.move(160, SCREEN_HEIGHT - 35)
			self.qw0.setVisible(True)
			self.qw1.setVisible(True)
			self.l1.setVisible(True)
			self.btn0_1.setVisible(True)
			self.btn0_2.setVisible(True)
			self.setMinimumSize(0, 0)
			self.setMaximumSize(16777215, 16777215)
			self.resize(1520, SCREEN_HEIGHT)
			# 调整内部组件以适应新的屏幕高度
			self._adjust_components_for_screen(SCREEN_HEIGHT)
			x_center = screen_x + int(SCREEN_WEIGHT / 2) - 760
			y_center = screen_y
			self.move(screen_x + int(SCREEN_WEIGHT / 2) - 760, screen_y - SCREEN_HEIGHT)
			self.updatecontent_for_mode()
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
			self.btn_00.setFixedHeight(10)
			self.btn_00.setFixedWidth(100)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #FFFFFF;
						border-radius: 4px;
						padding: 1px;
						color: #000000''')
			self.btn_00.move(0, 0)
			self.qw0.setVisible(False)
			self.qw1.setVisible(False)
			self.l1.setVisible(False)
			self.btn0_1.setVisible(False)
			self.btn0_2.setVisible(True)
			self.setFixedSize(100, 10)
			# 隐藏时移动到当前屏幕的顶部中央
			x_center = screen_x + int(SCREEN_WEIGHT / 2) - 50
			y_center = screen_y
			self.move(screen_x + int(SCREEN_WEIGHT / 2) - 50, screen_y + SCREEN_HEIGHT)

		self.move_window(x_center, y_center)
		self.qw0.raise_()
		self.qw1.raise_()
		self.btn_00.raise_()
		self.btn0_1.raise_()
		self.btn0_2.raise_()

	def closeEvent(self, event):
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

	def _confirm_notes_save(self):
		box = QMessageBox(self)
		box.setWindowTitle("Unsaved Notes")
		box.setText("Save changes to this note?")
		box.setStandardButtons(
			QMessageBox.StandardButton.Save
			| QMessageBox.StandardButton.Discard
			| QMessageBox.StandardButton.Cancel
		)
		box.setDefaultButton(QMessageBox.StandardButton.Save)
		result = box.exec()
		if result == QMessageBox.StandardButton.Save:
			return "save"
		if result == QMessageBox.StandardButton.Discard:
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
		box = QMessageBox(self)
		box.setWindowTitle("Note Title Changed")
		box.setText(f"The note title will change from \"{old_title}\" to \"{new_title}\".\nContinue saving?")
		box.setStandardButtons(
			QMessageBox.StandardButton.Save
			| QMessageBox.StandardButton.Cancel
		)
		box.setDefaultButton(QMessageBox.StandardButton.Save)
		result = box.exec()
		return result == QMessageBox.StandardButton.Save

	def _prompt_notes_reselect(self, folder, title):
		location = folder or "Unfiled"
		box = QMessageBox(self)
		box.setWindowTitle("Note Not Found")
		box.setText(
			f"Couldn't match the current note \"{title}\" in \"{location}\".\n"
			"Please reselect the note path."
		)
		box.setStandardButtons(
			QMessageBox.StandardButton.Ok
			| QMessageBox.StandardButton.Cancel
		)
		box.setDefaultButton(QMessageBox.StandardButton.Ok)
		result = box.exec()
		if result == QMessageBox.StandardButton.Ok:
			self.open_notes_folder_dialog()

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
		if self.topleftshow == 1:
			endhtml = self.md2html(previewtext)
			self.topleft.setHtml(endhtml)
		if self.toprightshow == 1:
			endbio = self.addb2(previewtext.replace('*', ''))
			endhtmlbio = self.md2html(endbio)
			self.topright.setHtml(endhtmlbio)

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
			app.setStyleSheet(style_sheet_ori + "\n" + font_override)
		if hasattr(self, "bottom") and hasattr(self, "topleft") and hasattr(self, "topright"):
			try:
				previewtext = self.bottom.toPlainText()
				if self.topleftshow == 1:
					self.topleft.setHtml(self.md2html(previewtext))
				if self.toprightshow == 1:
					endbio = self.addb2(previewtext.replace('*', ''))
					self.topright.setHtml(self.md2html(endbio))
			except Exception:
				pass

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
			if self.topleftshow == 1:
				endhtml = self.md2html(previewtext)
				self.topleft.setHtml(endhtml)
			if self.toprightshow == 1:
				endbio = self.addb2(previewtext.replace('*', ''))
				endhtmlbio = self.md2html(endbio)
				self.topright.setHtml(endhtmlbio)
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
			# set top left
			if self.topleftshow == 1:
				endhtml = self.md2html(previewtext)
				self.topleft.setHtml(endhtml)
			# set top right
			if self.toprightshow == 1:
				endbio = self.addb2(previewtext.replace('*', ''))
				endhtmlbio = self.md2html(endbio)
				self.topright.setHtml(endhtmlbio)
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
			# set left
			endhtml = self.md2html(text_open)
			self.topleft.setHtml(endhtml)
			# set right
			endbio = self.addb2(text_open.replace('*', ''))
			endhtmlbio = self.md2html(endbio)
			self.topright.setHtml(endhtmlbio)

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
		endhtml = self.md2html(previewtext)
		self.topleft.setHtml(endhtml)
		endbio = self.addb2(previewtext.replace('*', ''))
		endhtmlbio = self.md2html(endbio)
		self.topright.setHtml(endhtmlbio)

	def _set_notes_dirty(self, dirty):
		self.notes_dirty = bool(dirty)
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
		if not self.notes_active:
			self._set_notes_dirty(False)

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
			self.notes_wait_dialog = QDialog(self)
			self.notes_wait_dialog.setWindowTitle("Updating Notes")
			self.notes_wait_dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
			self.notes_wait_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
			self.notes_wait_dialog.destroyed.connect(self._notes_wait_dialog_destroyed)
			label = QLabel("Updating Notes, please wait...")
			layout = QVBoxLayout()
			layout.addWidget(label)
			self.notes_wait_dialog.setLayout(layout)
			self.notes_wait_dialog.setFixedSize(260, 90)
			qr = self.frameGeometry()
			cp = self.screen().availableGeometry().center()
			qr.moveCenter(cp)
			self.notes_wait_dialog.move(qr.topLeft())
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
			self.btn0_2.setStyleSheet('''
				QPushButton{
				border: transparent;
				background-color: transparent;
				border-image: url(/Applications/Watermelon.app/Contents/Resources/repeat2.png);
				}
				QPushButton:pressed{
				border: 1px outset grey;
				background-color: #0085FF;
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF
				}
				''')
		else:
			# self.btn_mode.setText('Mode: Local')
			self.btn0_2.setStyleSheet('''
				QPushButton{
				border: transparent;
				background-color: transparent;
				border-image: url(/Applications/Watermelon.app/Contents/Resources/repeat.png);
				}
				QPushButton:pressed{
				border: 1px outset grey;
				background-color: #0085FF;
				border-radius: 4px;
				padding: 1px;
				color: #FFFFFF
				}
			''')
			self._set_notes_active(False)
		self._apply_mode_visibility()
		self.updatecontent_for_mode()
		QTimer.singleShot(50, lambda: self._log_layout_state("toggle_after"))

	def open_notes_folder_dialog(self):
		if self.notes_folder_dialog:
			self.notes_folder_dialog.raise_()
			self.notes_folder_dialog.activateWindow()
			self.notes_folder_dialog.show()
			self.load_notes()
			return
		self.notes_folder_dialog = NotesFolderDialog(self)
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
		self._set_notes_active(True)
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
		rendered_html = markdown_to_html(note_md)
		if self.topleftshow == 1:
			self.topleft.setHtml(self.md2html("", pre_rendered_html=rendered_html))
		if self.toprightshow == 1:
			bio_text = self.addb2(note_md.replace('*', ''))
			bio_html = markdown_to_html(bio_text)
			self.topright.setHtml(self.md2html("", pre_rendered_html=bio_html))
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
			self._set_notes_dirty(True)
			return
		note_key = f"{folder}/{title}"
		delete_cache_file(note_key)
		note["body"] = note_html
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
		endhtml = self.md2html(previewtext)
		self.topleft.setHtml(endhtml)
		endbio = self.addb2(previewtext.replace('*', ''))
		endhtmlbio = self.md2html(endbio)
		self.topright.setHtml(endhtmlbio)

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
						  background-color: #F3F2EE;
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
		""" % (font_size, font_family, middlehtml)
		return html_content

class window4(QWidget):  # Customization settings
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):  # 设置窗口内布局
		self.setUpMainWindow()
		self.resize(640, 400)
		self.center()
		self.setWindowTitle('Customization settings')
		self.setFocus()
		self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

	def setUpMainWindow(self):
		wid0 = QWidget()
		lbl0 = QLabel("Manage recent files", self)
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
		self.btn4_1 = QPushButton('Delete', self)
		self.btn4_1.setMaximumHeight(20)
		self.btn4_1.setFixedWidth(250)
		self.btn4_1.setVisible(False)
		self.btn4_1.clicked.connect(self.delete_item)
		btn4_11 = QPushButton('Save', self)
		btn4_11.clicked.connect(self.SaveFeed)
		btn4_11.setMaximumHeight(20)
		btn4_11.setFixedWidth(250)
		b411 = QHBoxLayout()
		b411.setContentsMargins(0, 0, 0, 0)
		b411.addStretch()
		b411.addWidget(self.btn4_1)
		b411.addWidget(btn4_11)
		b411.addStretch()
		wid11.setLayout(b411)

		self.checkBox0 = QCheckBox('Automatically scroll simultaneously', self)
		self.checkBox0.setChecked(True)
		self.checkBox0.clicked.connect(self.auto_scroll)

		self.checkBox_top = QCheckBox('Always on top', self)
		self.checkBox_top.setChecked(w3.is_always_on_top())
		self.checkBox_top.clicked.connect(self.toggle_on_top)

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
		main_h_box.addStretch()
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
		background-color: #F3F2EE;
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
		background-color: #F3F2EE;
		color: #000000;
		font: 14pt Times New Roman;
}
	QFrame#webFrame{
		border: 1px solid grey;
		border-radius:4px;
		padding: 0px;
		background-clip: border;
		background-color: #F3F2EE;
}
	QWebEngineView{
		border: 0px;
}
	QListWidget{
        border: 1px solid grey;  
        border-radius:4px;
        padding: 1px 5px 1px 3px; 
        background-clip: border;
        background-color: #F3F2EE;
        color: #000000;
        font: 14pt Times New Roman;
}
	QMessageBox QPushButton {
		min-width: 100px;
		height: 20px;
}
'''


if __name__ == '__main__':
	w1 = window_about()
	w2 = window_update()
	w3 = window3()  # Main window
	w3.setAutoFillBackground(True)
	p = w3.palette()
	p.setColor(w3.backgroundRole(), QColor('#ECECEC'))
	w3.setPalette(p)
	w4 = window4()
	action1.triggered.connect(w3.addb)
	action2.triggered.connect(w3.pin_a_tab)
	action3.triggered.connect(w1.activate)
	action4.triggered.connect(w3.remb)
	action5.triggered.connect(w2.activate)
	action6.triggered.connect(w4.activate)
	action7.triggered.connect(w3.open_file_menu)
	btna4.triggered.connect(w3.pin_a_tab)
	w3.btn0_1.clicked.connect(w4.activate)
	w3.btn0_2.clicked.connect(w3.toggle_notes_mode)
	w3.set_textedit_font(w3._current_font_size, w3._current_font_family)
	app.exec()
