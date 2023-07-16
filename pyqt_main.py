#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import queue
import subprocess
import sys
import threading
import time
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,QMessageBox,
                             QPushButton, QSlider, QTextBrowser, QTextEdit,QCheckBox,
                             QVBoxLayout, QWidget,QComboBox,QLineEdit, QGridLayout, QFileDialog)
from qt_material import apply_stylesheet

from audio_process import MicAudio, SpeakerAudio, AudioContent
from asr import WhisperAsr, MyApiAsr
from chat_process import GPTResponder
from PyQt5.QtGui import QPixmap,QFont, QColor, QPalette
from setting import SettingsWindow
from register import RegisterWindow
from Login import LoginWindow


# Configure logging
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


# Define custom log function
def log_info(message):
    logging.info(message)


class ResourceObj:
    def __init__(self, audio_queue, transcriber, responder) -> None:
        self.transcriber = transcriber
        self.audio_queue = audio_queue
        self.responder = responder


class InitThread(QThread):
    signal_init_finished = pyqtSignal(ResourceObj)

    def __init__(self):
        super().__init__()

    def run(self):
        # try:
        log_info("init function is running")
        audio_queue = queue.Queue()
        user_audio_recorder = MicAudio()
        user_audio_recorder.record_into_queue(audio_queue)
        log_info("user_audio_recorder is ready")
        time.sleep(2)
        speaker_audio_recorder = SpeakerAudio()
        speaker_audio_recorder.record_into_queue(audio_queue)
        log_info("speaker_audio_recorder is ready")
        model = MyApiAsr()

        transcriber = AudioContent(user_audio_recorder.source, speaker_audio_recorder.source, model)
        transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(audio_queue,))
        transcribe.daemon = True
        transcribe.start()

        responder = GPTResponder()
        respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
        respond.daemon = True
        respond.start()
        res = ResourceObj(audio_queue, transcriber, responder)
        self.signal_init_finished.emit(res)
        log_info("init function signal is emited")
        # except Exception as e:
        #     logging.exception("Exception occurred in InitThread")
        #     log_info(e)


class MainWindow(QMainWindow):
    def __init__(self, transcriber=None, audio_queue=None):
        super().__init__()
        self.setWindowTitle("面试助手")
        self.setStyleSheet("background-color: #252422;")
        self.record = False
        self.file = "record.txt"
        menubar = self.menuBar()
        menubar.hide()
        self.font_size = 20
        self.transcriber = transcriber
        self.audio_queue = audio_queue
        self.transcript_textbox = QTextBrowser(self)
        self.transcript_textbox.setFontPointSize(self.font_size)
        self.transcript_textbox.setOpenLinks(False)
        self.transcript_textbox.anchorClicked.connect(self.on_anchor_clicked)
        self.transcript_textbox.setStyleSheet(
            "color: #FFFCF2; background-color: #252422;")
        self.transcript_textbox.setReadOnly(True)
        self.transcript_textbox.setLineWrapMode(QTextEdit.WidgetWidth)
        self.transcript_textbox.setText("面试助手初始化中\n请播放一段音频初始化模型!")
        self.response_textbox = QTextEdit(self)
        self.response_textbox.setFontPointSize(self.font_size)
        self.response_textbox.setStyleSheet(
            "color: #639cdc; background-color: #252422;")
        self.response_textbox.setReadOnly(True)
        self.response_textbox.setLineWrapMode(QTextEdit.WidgetWidth)

        self.clear_transcript_button = QPushButton("Clear Transcript", self)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.on_closed)

        self.setting_button = QPushButton("Setting", self)
        self.signIn_button = QPushButton("SignIn", self)
        self.Register_button = QPushButton("Register", self)
        self.setting_button.clicked.connect(self.on_setting_clicked)
        self.signIn_button.clicked.connect(self.on_signIn_clicked)
        self.Register_button.clicked.connect(self.on_Register_clicked)

        # create sub window
        self.settings_window = SettingsWindow(self)
        self.register_window = RegisterWindow(self)
        self.login_window = LoginWindow(self)


        vbox = QVBoxLayout()
        vbox.addWidget(self.transcript_textbox)
        vbox.addWidget(self.response_textbox)
        hbox = QHBoxLayout()
        hbox.addWidget(self.clear_transcript_button)
        hbox.addWidget(self.exit_button)
        hbox.addWidget(self.setting_button)  # Add setting button to layout
        hbox.addWidget(self.signIn_button)  # Add signInOrRegister button to layout
        hbox.addWidget(self.Register_button)

        hbox.addStretch()
        vbox.addLayout(hbox)
        vbox.addStretch()

        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        self.thread = InitThread()
        self.thread.signal_init_finished.connect(self.on_init_finished)

        self.thread.start()
        self.m_drag = False
        self.m_DragPosition = self.pos()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.m_drag:
            self.move(event.globalPos() - self.m_DragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.m_drag = False

    def on_closed(self):
        self.close()

    def on_init_finished(self, obj: ResourceObj):
        log_info("RECV INIT signal")
        self.transcriber = obj.transcriber
        self.audio_queue = obj.audio_queue
        self.clear_transcript_button.clicked.connect(lambda: self.clear_context())
        self.update_transcript_ui(obj.transcriber, self.transcript_textbox)
        self.update_response_ui(obj.responder, self.response_textbox)
        self.clear_transcript_button.clicked.connect(self.clear_context)
        log_info("INIT READY")
        self.transcript_textbox.setText("Initialization completed")

    def update_transcript_ui(self, transcriber, textbox):
        transcript_string = transcriber.get_transcript()+'\n'
        if self.record:
            with open(self.file, "a") as f:
                f.writelines(transcript_string)
        transcript_html = transcript_string.replace('\n', '<br>')
        textbox.setHtml(
            f"<a href=\"#{transcript_html}\" style=\"text-decoration: none; color: #FFFCF2;\">{transcript_html}</a>")
        QTimer.singleShot(300, lambda: self.update_transcript_ui(transcriber, textbox))

    def update_response_ui(self, responder, textbox):
        response = responder.response
        if self.record:
            with open(self.file, "a") as f:
                f.writelines(response)
        textbox.setFontPointSize(10)
        textbox.setPlainText(response)
        QTimer.singleShot(300, lambda: self.update_response_ui(responder, textbox))

    def clear_context(self):
        if self.transcriber is None or self.audio_queue is None:
            return
        self.transcriber.clear_transcript_data()
        self.transcript_textbox.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

    def on_anchor_clicked(self, url):
        transcript_string = url.fragment()
        log_info(f"Clicked transcript_string: {transcript_string}")

    def on_setting_clicked(self):
        self.hide()
        self.settings_window.show()

    def on_signIn_clicked(self):
        self.hide()
        self.login_window.show()

    def on_Register_clicked(self):
        self.hide()
        self.register_window.show()

    def update_settings(self, settings):
        # 在这里处理从SettingsWindow传递过来的设置参数
        # 处理字体大小
        font_size = settings.get('font_size', 10)
        font1 = self.transcript_textbox.font()
        font1.setPointSize(font_size)
        self.transcript_textbox.setFont(font1)
        font2 = self.response_textbox.font()
        font2.setPointSize(font_size)
        self.response_textbox.setFont(font2)

        # 处理背景颜色
        skin_color = settings.get('skin_color', 'white')
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(skin_color))
        self.setPalette(palette)

        # 处理透明度
        opacity = settings.get('opacity', 100) / 100
        self.setWindowOpacity(opacity)

        self.record = settings.get('record', False)
        if self.record:
            self.file = settings.get('folder'+'/', './') + "record.txt"

        print("更新设置：", settings)



def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        log_info("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
