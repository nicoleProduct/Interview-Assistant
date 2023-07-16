#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import librosa
import wave
import threading
import custom_speech_recognition as sr
import io
from datetime import timedelta
import pyaudiowpatch as pyaudio
import soundfile as sf
import os


RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False

PHRASE_TIMEOUT = 3.05
MAX_PHRASES = 10


class BaseAudio:
    def __init__(self, source, source_name):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source
        self.source_name = source_name

    def adjust_for_noise(self, device_name, msg):
        print(f"[INFO] Adjusting for ambient noise from {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment for {device_name}.")

    def record_into_queue(self, audio_queue):
        def record_callback(_, audio: sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((self.source_name, data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)


class MicAudio(BaseAudio):
    def __init__(self):
        super().__init__(source=sr.Microphone(sample_rate=16000), source_name="You")
        self.adjust_for_noise("Default Mic", "Please make some noise from the Default Mic...")


class SpeakerAudio(BaseAudio):
    def __init__(self):
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    print("[ERROR] No loopback device found.")

        source = sr.Microphone(speaker=True,
                               device_index=default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                               channels=default_speakers["maxInputChannels"])
        super().__init__(source=source, source_name="Speaker")
        self.adjust_for_noise("Default Speaker", "Please make or play some noise from the Default Speaker...")


class AudioContent:
    def __init__(self, mic_source, speaker_source, model):
        self.transcript_data = {"You": [], "Speaker": []}
        self.transcript_changed_event = threading.Event()
        self.audio_model = model
        self.audio_sources = {
            "You": {
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_mic_data
            },
            "Speaker": {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data
            }
        }

    def transcribe_audio_queue(self, audio_queue):
        while True:
            who_spoke, data, time_spoken = audio_queue.get()
            if who_spoke == "You":
                continue
            self.update_last_sample_and_phrase_status(who_spoke, data, time_spoken)

            source_info = self.audio_sources[who_spoke]

            text = ''
            path = os.path.join(os.getcwd(), "test.wav")

            source_info["process_data_func"](source_info["last_sample"], path)
            # 读取wav文件
            data, sr = librosa.load(path)
            data = librosa.resample(data, orig_sr=sr, target_sr=16000)
            sf.write(path, data, 16000)

            # text = self.audio_model.get_transcription(path)['text']
            text = self.audio_model.get_transcription(path)
            print("role ：", who_spoke, " speak: ", text)

            if text != '' and text.lower() != 'you':
                self.update_transcript(who_spoke, text, time_spoken)
                self.transcript_changed_event.set()

    def update_last_sample_and_phrase_status(self, who_spoke, data, time_spoken):
        source_info = self.audio_sources[who_spoke]
        if source_info["last_spoken"] and time_spoken - source_info["last_spoken"] > timedelta(seconds=PHRASE_TIMEOUT):
            source_info["last_sample"] = bytes()
            source_info["new_phrase"] = True
        else:
            source_info["new_phrase"] = False

        source_info["last_sample"] += data
        source_info["last_spoken"] = time_spoken

    def process_mic_data(self, data, temp_file_name):
        audio_data = sr.AudioData(data, self.audio_sources["You"]["sample_rate"],
                                  self.audio_sources["You"]["sample_width"])
        wav_data = io.BytesIO(audio_data.get_wav_data())
        with open(temp_file_name, 'w+b') as f:
            f.write(wav_data.read())

    def process_speaker_data(self, data, temp_file_name):
        # print("temp_file_name = ",temp_file_name)
        with wave.open(temp_file_name, 'wb') as wf:
            wf.setnchannels(self.audio_sources["Speaker"]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_sources["Speaker"]["sample_rate"])
            wf.writeframes(data)

    def update_transcript(self, who_spoke, text, time_spoken):
        source_info = self.audio_sources[who_spoke]
        transcript = self.transcript_data[who_spoke]

        if source_info["new_phrase"] or len(transcript) == 0:
            if len(transcript) > MAX_PHRASES:
                transcript.pop(-1)
            transcript.insert(0, (f"{who_spoke}: [{text}]\n\n", time_spoken))
        else:
            transcript[0] = (f"{who_spoke}: [{text}]\n\n", time_spoken)

    def get_transcript(self):
        combined_transcript = self.transcript_data["Speaker"]
        # combined_transcript = list(merge(
        #     self.transcript_data["You"], self.transcript_data["Speaker"],
        #     key=lambda x: x[1], reverse=True))
        combined_transcript = combined_transcript[:MAX_PHRASES]
        return "".join([t[0] for t in combined_transcript])

    def clear_transcript_data(self):
        self.transcript_data["You"].clear()
        self.transcript_data["Speaker"].clear()

        self.audio_sources["You"]["last_sample"] = bytes()
        self.audio_sources["Speaker"]["last_sample"] = bytes()

        self.audio_sources["You"]["new_phrase"] = True
        self.audio_sources["Speaker"]["new_phrase"] = True

