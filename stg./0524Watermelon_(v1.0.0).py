#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- encoding:UTF-8 -*-
# coding=utf-8
# coding:utf-8

# import codecs
from PyQt6.QtWidgets import (QWidget, QPushButton, QApplication,
                             QLabel, QHBoxLayout, QVBoxLayout, QLineEdit,
                             QSystemTrayIcon, QMenu, QComboBox, QDialog,
                             QDialogButtonBox, QMenuBar, QFrame, QFileDialog, QPlainTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
import PyQt6.QtGui
import sys
import webbrowser
import jieba
import pyperclip
import re
# import os
# from pathlib import Path

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Create the icon
icon = QIcon("wtmenu.icns")

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

'''action6 = QAction("🥳 Customization settings")
menu.addAction(action6)'''

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


class window0(QWidget):  # 增加说明页面(About)
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):  # 说明页面内信息
        lbl0 = QLabel('Watermelon', self)
        lbl0.move(142, 140)

        lbl = QLabel('''

                                        Version 1.0.0

                              This app is open-sourced. 
                        Please do not use it for business.
                                      本软件免费开源，
                                           请勿商用。






                © 2022 Ryan-the-hito. All rights reserved.
                ''', self)
        lbl.move(20, 135)

        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wtmenu.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setGeometry(150, 40, 100, 100)
        l1.setScaledContents(True)

        bt1 = QPushButton('The Author', self)
        bt1.clicked.connect(self.intro)
        bt1.move(205, 280)

        bt2 = QPushButton('Github Page', self)
        bt2.clicked.connect(self.homepage)
        bt2.move(100, 280)

        bt3 = QPushButton('Buy me a cup of coffee ☕', self)
        bt3.clicked.connect(self.donate)
        bt3.move(110, 310)

        font = PyQt6.QtGui.QFont()
        font.setFamily("Arial")
        font.setBold(True)
        font.setPointSize(20)
        lbl0.setFont(font)

        self.resize(400, 380)
        self.center()
        self.setWindowTitle('About')
        self.setFocus()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def intro(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Ryan-the-hito')

    def homepage(self):
        webbrowser.open('https://github.com/Ryan-the-hito/Watermelon')

    def donate(self):
        dlg = CustomDialog()
        dlg.exec()

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def activate(self):  # 设置窗口显示
        self.show()

    def addb(self):
        a = pyperclip.paste()
        if a != None:
            a = str(a)
            aj = jieba.cut(a, cut_all=False)
            paj = '/'.join(aj)
            saj = paj.split('/')

            def containenglish(str0):  # 判断是否包含英文字母
                import re
                return bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', str0))

            def is_contain_chinese(check_str):  # 判断是否包含中文字
                for ch in check_str:
                    if u'\u4e00' <= ch <= u'\u9fff':
                        return True
                return False

            def is_contain_num(str0):  # 判断是否包含数字
                import re
                return bool(re.search('[0-9０-９]', str0))

            def is_contain_symbol(keyword):
                if re.search(r"\W", keyword):
                    return True
                else:
                    return False

            for i in range(len(saj)):
                if containenglish(str(saj[i])) or is_contain_chinese(str(saj[i])) or is_contain_num(str(saj[i])):
                    if len(saj[i]) == 1:
                        saj[i] = '**' + saj[i] + '**'
                        i = i + 1
                        continue
                    if len(saj[i]) >= 2:
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

            def find_this(q, i):
                result = q[i]
                return result

            def find_next(q, i):
                result = q[i + 1]
                return result

            i = 0
            while i <= len(esj) - 1:
                if esj[i] == '¥' and not is_contain_symbol(str(esj[i - 1])):
                    esj = list(esj)
                    esj.insert(i, ' ')
                    esj = ''.join(esj)
                    i = i + 2
                    continue
                if esj[i] == '$' and not is_contain_symbol(str(esj[i - 1])):
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
                if is_contain_chinese(str(find_this(esj, i))) and containenglish(str(find_next(esj, i))):  # 从中文转英文
                    esj = list(esj)
                    esj.insert(i + 1, ' ')
                    esj = ''.join(esj)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_this(esj, i))) and is_contain_num(str(find_next(esj, i))):  # 从中文转数字
                    esj = list(esj)
                    esj.insert(i + 1, ' ')
                    esj = ''.join(esj)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(esj, i))) and is_contain_num(str(find_this(esj, i))):  # 从数字转中文
                    esj = list(esj)
                    esj.insert(i + 1, ' ')
                    esj = ''.join(esj)
                    i = i + 1
                    continue
                if is_contain_num(str(find_this(esj, i))) and containenglish(str(find_next(esj, i))):  # 从数字转英文
                    esj = list(esj)
                    esj.insert(i + 1, ' ')
                    esj = ''.join(esj)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(esj, i))) and containenglish(str(find_this(esj, i))):  # 从英文转数字
                    esj = list(esj)
                    esj.insert(i + 1, ' ')
                    esj = ''.join(esj)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(esj, i))) and containenglish(str(find_this(esj, i))):  # 从英文转中文
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

            pyperclip.copy(str(esj))
        else:
            pyperclip.copy('The clipboard is empty.')

    def remb(self):
        a = pyperclip.paste()
        if a != None:
            zui = a.replace('*', '')

            def containenglish(str0):  # 判断是否包含英文字母
                import re
                return bool(re.search('[a-zA-Zａ-ｚＡ-Ｚ]', str0))

            def is_contain_chinese(check_str):  # 判断是否包含中文字
                for ch in check_str:
                    if u'\u4e00' <= ch <= u'\u9fff':
                        return True
                return False

            def is_contain_num(str0):  # 判断是否包含数字
                import re
                return bool(re.search('[0-9０-９]', str0))

            def is_contain_symbol(keyword):
                if re.search(r"\W", keyword):
                    return True
                else:
                    return False

            def find_this(q, i):
                result = q[i]
                return result

            def find_next(q, i):
                result = q[i + 1]
                return result

            i = 0
            while i <= len(zui) - 1:
                if zui[i] == '¥' and not is_contain_symbol(str(zui[i - 1])):
                    zui = list(zui)
                    zui.insert(i, ' ')
                    zui = ''.join(zui)
                    i = i + 2
                    continue
                if zui[i] == '$' and not is_contain_symbol(str(zui[i - 1])):
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
                if is_contain_chinese(str(find_this(zui, i))) and containenglish(str(find_next(zui, i))):  # 从中文转英文
                    zui = list(zui)
                    zui.insert(i + 1, ' ')
                    zui = ''.join(zui)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_this(zui, i))) and is_contain_num(str(find_next(zui, i))):  # 从中文转数字
                    zui = list(zui)
                    zui.insert(i + 1, ' ')
                    zui = ''.join(zui)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(zui, i))) and is_contain_num(str(find_this(zui, i))):  # 从数字转中文
                    zui = list(zui)
                    zui.insert(i + 1, ' ')
                    zui = ''.join(zui)
                    i = i + 1
                    continue
                if is_contain_num(str(find_this(zui, i))) and containenglish(str(find_next(zui, i))):  # 从数字转英文
                    zui = list(zui)
                    zui.insert(i + 1, ' ')
                    zui = ''.join(zui)
                    i = i + 1
                    continue
                if is_contain_num(str(find_next(zui, i))) and containenglish(str(find_this(zui, i))):  # 从英文转数字
                    zui = list(zui)
                    zui.insert(i + 1, ' ')
                    zui = ''.join(zui)
                    i = i + 1
                    continue
                if is_contain_chinese(str(find_next(zui, i))) and containenglish(str(find_this(zui, i))):  # 从英文转中文
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
            pyperclip.copy(str(zui))
        else:
            pyperclip.copy('The clipboard is empty.')


class CustomDialog(QDialog):  # (About)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Thank you for your support!")

        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel('')

        m1 = QLabel('''
        Thank you for your kind support! 😊
        I will write more interesting apps! 🥳''', self)
        m1.move(10, 190)
        m1.resize(300, 60)

        l1 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('wechat_full.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l1.setPixmap(png)  # 在l1里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l1.setGeometry(20, 20, 180, 200)
        l1.setScaledContents(True)

        l2 = QLabel(self)
        png = PyQt6.QtGui.QPixmap('alipay_full.png')  # 调用QtGui.QPixmap方法，打开一个图片，存放在变量png中
        l2.setPixmap(png)  # 在l2里面，调用setPixmap命令，建立一个图像存放框，并将之前的图像png存放在这个框框里。
        l2.setGeometry(200, 20, 180, 200)
        l2.setScaledContents(True)

        self.resize(400, 300)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.center()

    def center(self):  # 设置窗口居中
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class window2(QWidget):  # 增加更新页面（Check for Updates）
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):  # 说明页面内信息

        lbl = QLabel('Current Version: 1.0.0', self)
        lbl.move(110, 75)

        lbl0 = QLabel('Check Now:', self)
        lbl0.move(30, 20)

        bt1 = QPushButton('Check Github', self)
        bt1.clicked.connect(self.upd)
        bt1.move(110, 15)

        bt2 = QPushButton('Check Baidu Net Disk', self)
        bt2.clicked.connect(self.upd2)
        bt2.move(110, 45)

        self.resize(300, 110)
        self.center()
        self.setWindowTitle('Check for Updates')
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


w0 = window0()
# w1 = window1()
w2 = window2()
# w3 = window3()
# w4 = window4()
action1.triggered.connect(w0.addb)
action3.triggered.connect(w0.activate)
action4.triggered.connect(w0.remb)
action5.triggered.connect(w2.activate)
# action6.triggered.connect(w4.activate)
app.exec()
