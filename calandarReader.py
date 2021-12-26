#!/usr/bin/env python3

from datetime import datetime
from os import path
from aiy.board import Board, Led
#from aiy.cloudspeech import CloudSpeechClient
import pandas as pd
import pyttsx3
import speech_recognition as sr
import re
import json

LOCATION = 'Computational Foundry 104 PC'
COLUMN_LIST: list


# write to JSON file
def write_to_json(transcript_from_speech: str | None, output: str, success: bool = False):
    new_event = {
        'date': datetime.now().strftime('%x'),
        'time': datetime.now().strftime('%X'),
        'speech': transcript_from_speech,
        'output': output,
        'success': success}

    with open('data.json', 'r+') as json_file:
        data = json.load(json_file)
        data.append(new_event)
        json_file.seek(0)
        json_file.write(json.dumps(data))
        json_file.truncate()
        json_file.close()

# microphone set up


def listen():
    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    recognizer.energy_threshold = 653
    recognizer.dynamic_energy_threshold = True

    return speech_from_mic(recognizer, microphone)


def speech_from_mic(audio_recognizer, usb_microphone):
    """takes speech from microphone turn to text
    returns a directory with one of 3 values
    "success" : boolean saying API request was successful or not
    "error": none if no errors otherwise a string containing the error
    "transcription": none if speech could not be transcribed else a string
    """

    # check that recognizer and microphone are appropriate types
    if not isinstance(audio_recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(usb_microphone, sr.Microphone):
        raise TypeError("microphone object must be of sr.Microphone")

    # we adjust ambient sensitivity to ambient noise
    # then we record from microphone and save as var audio
    with usb_microphone as source:
        audio_recognizer.adjust_for_ambient_noise(source)
        audio = audio_recognizer.listen(source)

    # setting up response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recoding (audio)
    # if a RequestError or unknown value error exception is caught,
    #   update the response object
    try:
        response["transcription"] = audio_recognizer.recognize_google(
            audio, language="en-GB")
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was untranslatable
        response["error"] = "Unable to recognize speech"

    return response


def text_to_speech(text) -> None:
    """
    takes a string and plays said string in speech
    :param text: string of what will be said
    :return: nothing
    """
    # TODO: slow talk speed
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


# lab set up
class LabClass:
    name: str
    duration: str
    location = []

    # TODO: save when lab starts or ends

    def __init__(self, name, duration, location) -> None:
        self.name = name
        self.duration = duration
        if ',' in location:
            self.location = [x.strip() for x in location.split(',')]
        else:
            self.location.append(str(location).strip())

    def __str__(self) -> str:
        return 'Module:\t\t' + self.name + '\n' + 'Duration:\t' + self.duration + '\n' + 'Location:\t' + str(
            self.location)


# Store column names as they change each week
# index 0 of columns is not needed


def get_timetable():
    # TODO: get timetable from website
    # try website if not use html
    timetable = pd.read_html(open('FSE Intranet - Timetable.html', 'r').read())
    timetable = timetable[0]
    global COLUMN_LIST
    COLUMN_LIST = timetable.columns[1:6]
    return timetable


# TODO: get lab slot for given times, location etc.
def get_lab_slot():
    timetable = get_timetable()

    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))

    # If it's the weekend or it's before 9am and after 6pm
    if day > 5 or hour < 9 or hour > 18:
        # TODO: tell people to go home when its closed
        return []

    # noinspection PyTypeChecker
    comma_line = str(timetable[get_column_name(day)][get_row(hour)])
    print(comma_line)
    comma_line = re.split('MA-|CS', comma_line)
    list_of_labs = []
    for item in comma_line:
        x = item.split('  ')
        x = list(filter(None, x))
        if not x:
            continue
        if x[0] == '-009' or x[0] == '-181':
            list_of_labs.append(LabClass('MA' + x[0], x[2], x[3]))
        elif len(x) == 4:
            list_of_labs.append(LabClass('CS' + x[0], x[2], x[3]))
        elif len(x) == 3:
            list_of_labs.append(LabClass('CS' + x[0], x[1], x[2]))

    return list_of_labs


def get_column_name(num) -> list:
    return COLUMN_LIST[num - 1]


def get_row(num) -> int:
    # 9am == 0
    # 5pm == 8
    return num - 9


def lab_free(location=LOCATION) -> bool:
    list_of_labs = get_lab_slot()
    for x in list_of_labs:
        if location in x.location:
            text_to_speech("The lab is not free")
            return False
        else:
            text_to_speech("The lab is free")
            return True


if __name__ == '__main__':
    # TODO: create function to get button input
    if input('press a key'):
        speech = listen()
        if speech['error']:
            write_to_json(None, speech['error'])
        else:
            txt = speech['transcription'].lower()
            if 'is the lab free' in txt:
                if lab_free():
                    write_to_json(txt, "The lab is free", True)
                else:
                    write_to_json(txt, "The lab is not free", True)
            else:
                write_to_json(txt, "I don't understand")

# TODO: Get lab locations
