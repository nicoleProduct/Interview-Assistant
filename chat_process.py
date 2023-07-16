#!/usr/bin/env python
# -*- coding: utf-8 -*-


import openai
from utils import OPENAI_API_KEY, create_prompt, INITIAL_RESPONSE
import time, sys, requests, json

openai.api_key = OPENAI_API_KEY


def get_each_response(transcript):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=[{"role": "system", "content": create_prompt(transcript)}],
        temperature=0.0,
        stream=True
    )
    # create variables to collect the stream of chunks
    collected_chunks = []
    collected_messages = []
    collected_messages_str = ''
    # iterate through the stream of events
    for chunk in response:
        collected_chunks.append(chunk)  # save the event response
        chunk_message = chunk['choices'][0]['delta']  # extract the message
        collected_messages.append(chunk_message)  # save the message
        collected_messages_str = ''.join([m.get('content', '') for m in collected_messages])
        sys.stdout.flush()
    return collected_messages_str


def get_chatglm(transcript):
    url = "http://192.168.31.158:8000"
    headers = {'Content-Type': 'application/json'}
    data = {"prompt": create_prompt(transcript), "history": []}

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return json.loads(response.text)["response"]


def get_poeres(transcript):
    poe_url = 'http://192.168.31.158:10010/poe_chat'
    response = requests.post(poe_url, data={'message': transcript})
    result = response.content.decode('utf-8')
    return result


def generate_response_from_transcript(transcript):
    try:
        # res = get_each_response(transcript)
        res = get_poeres(transcript)
        return res
    except Exception as e:
        print(e)
        return ''


class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()

                transcriber.transcript_changed_event.clear()
                transcript_string = transcriber.get_transcript()
                response = generate_response_from_transcript(transcript_string)

                end_time = time.time()  # Measure end time
                execution_time = end_time - start_time  # Calculate the time it took to execute the function

                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval
