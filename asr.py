#!/usr/bin/env python
# -*- coding: utf-8 -*-
import whisper, requests
import os
import torch
from aip import AipSpeech
from utils import APP_ID, API_KEY, SECRET_KEY


class WhisperAsr:
    def __init__(self):
        self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'resources/base.pt'))
        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    def get_transcription(self, wav_file_path):
        try:
            result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available())
        except Exception as e:
            print(e)
            return ''
        return result


class MyApiAsr:
    def __init__(self):
        self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'resources/base.pt'))
        self.upload_url = "http://192.168.31.158:10010/upload"
        self.url = 'http://192.168.31.158:10010/whisper'
        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    def get_transcription(self, wav_file_path):
        try:
            # 将文件上传到服务器
            with open(wav_file_path, 'rb') as audio_file:
                response = requests.post(self.upload_url, files={'file': audio_file})
            # 检查上传是否成功
            if response.status_code == 200:
                # print("上传成功")
                server_file_path = response.text  # 假设服务器返回上传文件的路径
            else:
                # print("上传失败")
                server_file_path = None
            if server_file_path:
                response = requests.post(self.url, data={'filepath': server_file_path})
                result = response.content.decode('utf-8')
                print("识别结果：", result)
            else:
                print("无法识别音频文件，因为上传失败")
                return ''
        except Exception as e:
            print(e)
            return ''
        return result


def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()


def wav2pcm(input_dir, out_dir):
    with open(input_dir, 'rb') as wavfile:
        ori_data = wavfile.read()  ## 读出来是裸流bytes数据
        wavfile.close()
    with open(out_dir, 'wb') as pcmfile:
        pcmfile.write(ori_data)
        pcmfile.close()


class BaiduAsr:
    def __init__(self):
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    def get_transcription(self, wav_file_path):
        try:
            # 识别本地文件
            res = self.client.asr(get_file_content(wav_file_path), 'wav', 16000, {
                'dev_pid': 1537,
            })
        except Exception as e:
            print(e)
            return ''
        return res['result'][0].strip()
