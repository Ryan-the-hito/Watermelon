#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

import codecs
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
							 QLabel, QHBoxLayout, QVBoxLayout, QLineEdit,
							 QSystemTrayIcon, QMenu, QComboBox, QDialog,
							 QDialogButtonBox, QMenuBar, QFrame, QFileDialog, QPlainTextEdit, QSplitter, QTextEdit)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect
from PyQt6.QtGui import QAction, QIcon, QColor
import PyQt6.QtGui
import sys
import webbrowser
import jieba
import re
import urllib3
import logging
import requests
from bs4 import BeautifulSoup
import html2text
import subprocess
import os
from pathlib import Path
import markdown2
from datetime import datetime

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BasePath = '/Applications/Watermelon.app/Contents/Resources/'
#BasePath = ''

# Create the icon
icon = QIcon(BasePath + "wtmenu.icns")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()
action1 = QAction("🦾 Bold Text!")
menu.addAction(action1)

action4 = QAction("💪 Unbold Text!")
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
		lbl1 = QLabel('Version 2.0.0', self)
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
		lbl6 = QLabel('© 2022-2023 Ryan-the-hito. All rights reserved.', self)
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

		self.lbl = QLabel('Current Version: v2.0.0', self)
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


class window3(QWidget):  # 主窗口
	def __init__(self):
		super().__init__()
		self.initUI()
		self.dragPosition = None

	def initUI(self):
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
		SCREEN_HEIGHT = int(self.screen().availableGeometry().height())
		self.setFixedSize(1520, SCREEN_HEIGHT)
		self.i = 1

		home_dir = str(Path.home())
		tarname1 = "WatermelonAppPath"
		fulldir1 = os.path.join(home_dir, tarname1)
		if not os.path.exists(fulldir1):
			os.mkdir(fulldir1)

		self.topleft = QTextEdit(self)
		self.topleft.setMaximumHeight(SCREEN_HEIGHT - 200)
		self.topleft.setReadOnly(True)
		self.topleft.setDisabled(True)

		self.topright = QTextEdit(self)
		self.topright.setMaximumHeight(SCREEN_HEIGHT - 200)
		self.topright.setReadOnly(True)
		self.topright.setDisabled(True)

		self.bottom = QTextEdit(self)
		self.bottom.setFixedWidth(1235)
		self.bottom.textChanged.connect(self.text_change)
		self.scrollbar = self.bottom.verticalScrollBar()
		self.scrollbar.valueChanged.connect(self.scrollchanged)

		splitter1 = QSplitter(Qt.Orientation.Horizontal)
		splitter1.addWidget(self.topleft)
		splitter1.addWidget(self.topright)

		splitter2 = QSplitter(Qt.Orientation.Vertical)
		splitter2.addWidget(splitter1)
		splitter2.addWidget(self.bottom)
		splitter2.setSizes([SCREEN_HEIGHT - 200, 100])
		splitter2.setStyleSheet('''
					QSplitter::handle{
					border: transparent;
					background-color: transparent;
					border-image: url(/Applications/Watermelon.app/Contents/Resources/middle6.png);
					height: 20px;
					border-radius: 4px;
					}
					''')
		splitter1.setStyleSheet('''
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
		hbox.addWidget(splitter2)
		hbox.addStretch()
		self.qw0.setLayout(hbox)
		self.qw0.setFixedHeight(SCREEN_HEIGHT - 118)

		self.l1 = QLabel(self)
		png = PyQt6.QtGui.QPixmap(
			BasePath + 'bottom7.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
		scaled_png = png.scaled(1478, 215, transformMode=Qt.TransformationMode.SmoothTransformation)
		self.l1.setPixmap(scaled_png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
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
				f0.write('This is your very first note stored in [Home]/WatermelonAppPath/Note 001.md. \n\n**Just write what you want and start enjoying typing!**')
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

		self.btn_sub3 = QPushButton('Save', self)
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

		self.setStyleSheet(style_sheet_ori)
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

		self.assigntoall()

		w2.checkupdate()
		if w2.lbl2.text() != 'No Intrenet' and 'ready' in w2.lbl2.text():
			w2.show()

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

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.dragPosition = event.globalPosition().toPoint() - self.pos()

	def mouseMoveEvent(self, event):
		if self.dragPosition is None:
			return
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.dragPosition)

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
		SCREEN_WEIGHT = int(self.screen().availableGeometry().width())
		SCREEN_HEIGHT = int(self.screen().availableGeometry().height())
		x_center = 0
		y_center = 0
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
			self.qw0.setVisible(True)
			self.qw1.setVisible(True)
			self.l1.setVisible(True)
			self.setFixedSize(1520, SCREEN_HEIGHT)
			x_center = int(SCREEN_WEIGHT / 2) - 760
			y_center = 0
			self.move(int(SCREEN_WEIGHT / 2) - 760, 0 - SCREEN_HEIGHT)
			self.btn_00.move(160, SCREEN_HEIGHT - 35)
		if self.i % 2 == 0:  # hide
			btna4.setChecked(False)
			self.btn_00.setFixedHeight(10)
			self.btn_00.setFixedWidth(100)
			self.btn_00.setStyleSheet('''
						border: 1px outset grey;
						background-color: #FFFFFF;
						border-radius: 4px;
						padding: 1px;
						color: #000000''')
			self.qw0.setVisible(False)
			self.qw1.setVisible(False)
			self.l1.setVisible(False)
			self.setFixedSize(100, 10)
			x_center = int(SCREEN_WEIGHT / 2) - 50
			y_center = 10
			self.move(int(SCREEN_WEIGHT / 2) - 50, SCREEN_HEIGHT)
			self.btn_00.move(0, 0)

		self.move_window(x_center, y_center)
		self.show()
		self.qw0.raise_()
		self.qw1.raise_()
		self.btn_00.raise_()

	def text_change(self):
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
			endhtml = self.md2html(previewtext)
			self.topleft.setHtml(endhtml)
			# set top right
			endbio = self.addb2(previewtext.replace('*', ''))
			endhtmlbio = self.md2html(endbio)
			self.topright.setHtml(endhtmlbio)

	def scrollchanged(self):
		if self.bottom.verticalScrollBar().maximum() != 0:
			proportion = self.bottom.verticalScrollBar().value() / self.bottom.verticalScrollBar().maximum()
			tar_pro = int(self.topleft.verticalScrollBar().maximum() * proportion)
			self.topleft.verticalScrollBar().setValue(tar_pro)
			tar_pro2 = int(self.topright.verticalScrollBar().maximum() * proportion)
			self.topright.verticalScrollBar().setValue(tar_pro2)

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
		self.topleft.clear()
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
		self.bottom.clear()
		self.topleft.clear()
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
		w3.widget0.currentIndexChanged.disconnect(w3.index_change)
		w3.bottom.textChanged.disconnect(w3.text_change)

		self.bottom.clear()
		self.topleft.clear()
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

	def md2html(self, mdstr):
		extras = ['code-friendly', 'fenced-code-blocks', 'footnotes', 'tables', 'code-color', 'pyshell', 'nofollow',
				  'cuddled-lists', 'header ids', 'nofollow']

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
		ret = markdown2.markdown(mdstr, extras=extras)
		return html % ret

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
		b40.setContentsMargins(10, 10, 10, 10)
		b40.addStretch()
		b40.addWidget(lbl0)
		b40.addStretch()
		wid0.setLayout(b40)

		wid1 = QWidget()
		self.text_feed = QTextEdit(self)
		self.text_feed.setFixedWidth(550)
		self.text_feed.setFixedHeight(340)
		self.text_feed.setPlaceholderText('A record a line, with the first part being the title, and the second being the path.')
		b41 = QHBoxLayout()
		b41.setContentsMargins(10, 10, 10, 10)
		b41.addWidget(self.text_feed)
		wid1.setLayout(b41)

		wid11 = QWidget()
		btn4_11 = QPushButton('Save', self)
		btn4_11.clicked.connect(self.SaveFeed)
		btn4_11.setMaximumHeight(20)
		btn4_11.setFixedWidth(250)
		b411 = QHBoxLayout()
		b411.setContentsMargins(10, 10, 10, 10)
		b411.addStretch()
		b411.addWidget(btn4_11)
		b411.addStretch()
		wid11.setLayout(b411)

		main_h_box = QVBoxLayout()
		main_h_box.addWidget(wid0)
		main_h_box.addWidget(wid1)
		main_h_box.addWidget(wid11)
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
		self.text_feed.setText(exsfeeds)

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

	def activate(self):  # 设置窗口显示
		self.show()
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
		self.text_feed.setText(exsfeeds)

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

		part1 = self.text_feed.toPlainText()
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
	app.setStyleSheet(style_sheet_ori)
	app.exec()
