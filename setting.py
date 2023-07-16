# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setting.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import  QMainWindow,QApplication
import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, \
    QComboBox, QHBoxLayout, QCheckBox, QFileDialog, QGridLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class SettingsWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.settings = {}
        self.initUI()


    def initUI(self):
        self.setWindowTitle('设置界面')
        self.resize(800, 600)

        # 设置背景图片
        # label = QLabel(self)
        # pixmap = QPixmap('./resources/pic_setting.png')
        # label.setPixmap(pixmap)
        # label.resize(pixmap.width(), pixmap.height())
        # label.lower()

        grid = QGridLayout()

        # 设置字体大小
        font_label = QLabel('设置字体大小')
        font_combo = QComboBox()
        font_combo.addItem('10')
        font_combo.addItem('15')
        font_combo.addItem('20')
        font_combo.currentTextChanged.connect(lambda text: self.settings.update({"font_size": int(text)}))
        self.settings["font_size"] = int(font_combo.currentText())  # 初始化设置字典
        grid.addWidget(font_label, 0, 0)
        grid.addWidget(font_combo, 0, 1)

        # 肤色
        skin_label = QLabel('肤色')
        skin_combo = QComboBox()
        skin_combo.addItem('white')
        skin_combo.addItem('dark')
        skin_combo.currentTextChanged.connect(lambda text: self.settings.update({"skin_color": text}))
        self.settings["skin_color"] = skin_combo.currentText()
        grid.addWidget(skin_label, 1, 0)
        grid.addWidget(skin_combo, 1, 1)

        # 透明度
        opacity_label = QLabel('透明度')
        opacity_combo = QComboBox()
        opacity_combo.addItem('100')
        opacity_combo.addItem('50')
        opacity_combo.addItem('30')
        opacity_combo.currentTextChanged.connect(lambda text: self.settings.update({"opacity": int(text)}))
        self.settings["opacity"] = int(opacity_combo.currentText())
        grid.addWidget(opacity_label, 2, 0)
        grid.addWidget(opacity_combo, 2, 1)

        # 语言识别方法选择
        recognition_label = QLabel('语言识别方法选择')
        recognition_combo = QComboBox()
        recognition_combo.addItem('使用本地模型')
        recognition_combo.addItem('使用API')
        recognition_combo.currentTextChanged.connect(lambda text: self.settings.update({"recognition": text}))
        self.settings["recognition"] = recognition_combo.currentText()
        grid.addWidget(recognition_label, 3, 0)
        grid.addWidget(recognition_combo, 3, 1)

        # 答案来源选择
        source_label = QLabel('答案来源选择')
        source_combo = QComboBox()
        source_combo.addItem('使用已有账号')
        source_combo.addItem('使用服务器模型')
        source_combo.currentTextChanged.connect(lambda text: self.settings.update({"source": text}))
        self.settings["source"] = source_combo.currentText()
        grid.addWidget(source_label, 4, 0)
        grid.addWidget(source_combo, 4, 1)

        # 可选方向
        direction_label = QLabel('可选方向')
        direction_combo = QComboBox()
        direction_combo.addItem('C++')
        direction_combo.addItem('Python')
        direction_combo.currentTextChanged.connect(lambda text: self.settings.update({"direction": text}))
        self.settings["direction"] = direction_combo.currentText()
        grid.addWidget(direction_label, 5, 0)
        grid.addWidget(direction_combo, 5, 1)

        # 可选语言
        language_label = QLabel('可选语言')
        language_combo = QComboBox()
        language_combo.addItem('中文')
        language_combo.addItem('英文')
        language_combo.currentTextChanged.connect(lambda text: self.settings.update({"language": text}))
        self.settings["language"] = language_combo.currentText()
        grid.addWidget(language_label, 6, 0)
        grid.addWidget(language_combo, 6, 1)

        # 记录设置
        record_checkbox = QCheckBox('记录设置', self)
        record_checkbox.stateChanged.connect(self.toggle_record_button)
        record_checkbox.stateChanged.connect(lambda state: self.settings.update({"record": state == Qt.Checked}))
        self.settings["record"] = record_checkbox.isChecked()
        grid.addWidget(record_checkbox, 7, 0)

        # 选择文件夹按钮
        self.folder_button = QPushButton('选择文件夹', self)
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_button.setEnabled(False)
        grid.addWidget(self.folder_button, 7, 1)

        hbox = QHBoxLayout()
        btn_ok = QPushButton('确定', self)
        btn_cancel = QPushButton('回到主界面', self)
        hbox.addWidget(btn_ok)
        hbox.addWidget(btn_cancel)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        btn_cancel.clicked.connect(self.show_parent)
        btn_ok.clicked.connect(self.apply_settings)

    def toggle_record_button(self, state):
        if state == Qt.Checked:
            self.folder_button.setEnabled(True)
        else:
            self.folder_button.setEnabled(False)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            self.settings["folder"] = folder
            print(f"选择的文件夹: {folder}")

    def show_parent(self):
        self.hide()
        self.parent.show()

    def resizeEvent(self, event):
        # 更新背景图片大小
        label = self.findChild(QLabel)
        label.resize(self.size())

    def apply_settings(self):
        self.parent.update_settings(self.settings)