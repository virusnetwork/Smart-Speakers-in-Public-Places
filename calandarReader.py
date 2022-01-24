#!/usr/bin/env python3

from datetime import datetime
import pandas as pd
import pyttsx3
import speech_recognition as sr
import re
import json
import RPi.GPIO as GPIO
import time
import logging
import tempfile
import time
from aiy.voice.audio import AudioFormat, play_wav, record_file

LOCATION = 'Computational Foundry 104 PC'
COLUMN_LIST: list
POSSIBLE_INPUT = ('is this lab free', 'is the lab free', 'is the lamb free')
LABS = ('203', '204', '104', '103')

# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# set GPIO Pins
GPIO_TRIGGER = 7
GPIO_ECHO = 8

# set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='myapp.log',
                    filemode='w')


def activate_system() -> bool:

    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    # * distance is represents cm
    return distance < 15.0

# write to JSON file


def write_to_json(transcript_from_speech: str, output: str, success: bool = False):
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


def speech_to_text():
    with tempfile.NamedTemporaryFile() as f:
        record_file(AudioFormat.CD, filename=f.name, filetype='wav',
                    wait=lambda: time.sleep(4))
        r = sr.Recognizer()
        file_audio = sr.AudioFile(f.name)

        with file_audio as source:
            audio_text = r.record(source)
       
        return r.recognize_google(audio_text, language='en_GB')
    


def text_to_speech(text) -> None:
    """
    takes a string and plays said string in speech
    :param text: string of what will be said
    :return: nothing
    """
    # TODO: slow talk speed
    # BUG: Works once then won't work again
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
def get_lab_slots() -> list:
    timetable = get_timetable()

    # Monday = 1, Friday = 5
    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))

    # If it's the weekend or it's before 9am and after 6pm
    if day > 5 or hour < 9 or hour > 18:
        # TODO: tell people to go home when its closed
        return []

    comma_line = str(timetable[get_column_name(day)][get_row(hour)])

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

# TODO: create function to find WHAT labs are free


def lab_free(location=LOCATION) -> bool:
    list_of_labs = get_lab_slots()
    if(list_of_labs):
        for x in list_of_labs:
            if location in x.location:
                text_to_speech("The lab is not free")
                return False

    # if list of labs is empty or given lab is not in lab
    text_to_speech("The lab is free")
    return True


def what_labs_are_free():
    # get labs
    list_of_labs = get_lab_slots()

    # get used location
    in_use_labs = []
    for x in list_of_labs:
        in_use_labs.append(x.location)

    # return elements not in used location
    free_labs = []
    for y in LABS:
        if y not in in_use_labs:
            free_labs.append(y)

    if free_labs:
        speech = ''
        for z in free_labs:
            speech = speech + ' CF' + z
        text_to_speech(speech)

    else:
        text_to_speech('No labs are free at the momement')


def main():
    while True:
        if(activate_system()):
            logging.info("System Activated")
            text_to_speech("How can i help?")
            logging.info("start listing")
            try:
                speech = speech_to_text()
            except sr.UnknownValueError:
                logging.error("speech error: uninteligable")
                text_to_speech("I'm sorry, I don't undertsand")
                write_to_json('', 'UnknownValueError')
                continue

            except sr.RequestError:
                logging.error("speech error: RequestError")
                text_to_speech("I'm sorry, I'm not connected to the internet")
                write_to_json('', 'RequestError')
                continue
            
            logging.info("speech understood")
            speech = speech.lower()
            logging.info(speech)
            if 'what' in speech and 'free' in speech:
                what_labs_are_free()
            elif 'is the lab free' or 'is the lamb free' in speech:
                print("got this far")
                if lab_free():
                    write_to_json(speech, "The lab is free", True)
                else:
                    write_to_json(speech, "The lab is not free", True)
            else:
                text_to_speech("I don't know how to answer")
                write_to_json(speech, "unhandled input")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()

# TODO: Get lab locations
# TODO: Which labs are free
