#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, \
    QComboBox, QHBoxLayout, QCheckBox, QFileDialog, QGridLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class LoginWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle('登录界面')

        # 设置窗口的初始大小
        self.resize(800, 600)

        # 设置背景图片
        label = QLabel(self)
        # pixmap = QPixmap('./resources/picture_s.png')
        # label.setPixmap(pixmap)
        # label.resize(pixmap.width(), pixmap.height())
        # label.lower()

        # 用户名标签和文本框
        username_label = QLabel('用户名', self)
        self.username_edit = QLineEdit(self)
        username_label.setGeometry(300, 200, 200, 30)
        self.username_edit.setGeometry(300, 240, 200, 30)

        # 密码标签和文本框
        password_label = QLabel('密码', self)
        self.password_edit = QLineEdit(self)
        password_label.setGeometry(300, 280, 200, 30)
        self.password_edit.setGeometry(300, 320, 200, 30)

        # 确定和取消按钮
        btn_ok = QPushButton('确定', self)
        btn_cancel = QPushButton('回到主界面', self)
        btn_ok.setGeometry(300, 360, 90, 30)
        btn_cancel.setGeometry(410, 360, 100, 30)
        btn_ok.clicked.connect(self.login)
        btn_cancel.clicked.connect(self.show_parent)

    def show_parent(self):
        self.hide()
        self.parent.show()

    def resizeEvent(self, event):
        # 更新背景图片大小
        label = self.findChild(QLabel)
        label.resize(self.size())

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        if self.check_credentials(username, password):
            print("登录成功，返回主界面")
            self.show_parent()
        else:
            QMessageBox.warning(self, "错误", "用户名或者密码不正确，请重新输入")

    def check_credentials(self, username, password):
        with open('register.txt', 'r') as f:
            for line in f:
                user, passw, tele = line.strip().split(',')
                if user == username and passw == password:
                    return True
        return False