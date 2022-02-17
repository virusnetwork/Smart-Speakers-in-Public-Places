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
from aiy.voice.audio import AudioFormat, record_file

#TODO: better name for file

LOCATION = str("Computational Foundry 104 PC")
COLUMN_LIST: list
POSSIBLE_INPUT = ['is this lab free', 'is the lab free',
                  'is the lamb free', 'lab free', 'lab avaible', 'this', 'lab']
LABS = [203, 204, 104, 103]

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

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


# lab set up
class LabClass:
    name: str
    duration: str
    location = []

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
    # ! unuable to get html from website, have to manually update it
    timetable = pd.read_html(open('FSE Intranet - Timetable.html', 'r').read())
    timetable = timetable[0]
    global COLUMN_LIST
    COLUMN_LIST = timetable.columns[1:6]
    return timetable


def get_lab_slots() -> list:

    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))

    timetable = get_timetable()

    # Monday = 1, Friday = 5

    # If it's the weekend or it's before 9am and after 6pm
    if day > 5 or hour < 9 or hour > 17:
        return ['closed']

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


def lab_free(location=LOCATION):

    list_of_labs = get_lab_slots()
    if list_of_labs == ['closed']:
        text_to_speech("The lab is closed")
        return ("The lab is closed", True)

    if type(location) is int:
        if int(location) in LABS:
            num = location
            location = 'Computational Foundry ' + str(location) + ' PC'

        else:
            text_to_speech('I do not know that lab')
            return ('I do not know lab' + location, False)
    elif location == LOCATION:
        num = 104
    else:
        raise ValueError('Mishandled input in lab_free function')

    if(list_of_labs):
        for x in list_of_labs:
            if location in x.location:
                text_to_speech(str(num) + " is not free")
                return (str(num) + " is not free", True)

    text_to_speech(str(num) + " is free")
    return (str(num) + " is free", True)


def what_labs_are_free():
    # get labs
    list_of_labs = get_lab_slots()
    if list_of_labs == ['closed']:
        text_to_speech("The lab is closed")
        return ("The lab is closed", True)

    # get used location
    in_use_labs = []
    for x in list_of_labs:
        for a in x.location:
            in_use_labs.append(a)

    # remove duplicate labs
    in_use_labs = list(set(in_use_labs))

    # return elements not in used location
    free_labs = []
    for y in LABS:
        if 'Computational Foundry ' + str(y) + ' PC' not in in_use_labs:
            free_labs.append(y)

    speech = ""
    if free_labs:
        for z in free_labs:
            speech += ' CF' + str(z)

    else:
        speech = 'No labs are free at the momement'

    text_to_speech(speech)
    return speech


def has_numbers(string) -> bool:
    return any(char.isdigit() for char in string)


def get_Speech():
    try:
        speech = speech_to_text()
        return speech.lower()
    except sr.UnknownValueError:
        logging.error("speech error: uninteligable")
        text_to_speech("I'm sorry, I don't undertsand")
        write_to_json('', 'UnknownValueError')
        return ''

    except sr.RequestError:
        logging.error("speech error: RequestError")
        text_to_speech("I'm sorry, I'm not connected to the internet")
        write_to_json('', 'RequestError')
        return ''

    except Exception as e:
        logging.error("Unknown error: " + e)
        text_to_speech("I'm sorry, an error occured")
        write_to_json('', '"Unknown error: " + e')
        return ''


def get_num(string):
    emp_str = ""
    for m in string:
        if m.isdigit():
            emp_str = emp_str + m

    num = int(emp_str)

    if len(str(num)) == 3:
        if num in LABS:
            return num
    else:
        if len(str(num)) % 3 == 0:
            parts = [str(num)[i:i+3] for i in range(0, len(str(num)), 3)]
            temp = list(map(int, parts))[0]
            if temp in LABS:
                return temp

    return -1


def handle_speech(speech):
    #TODO: Improve handling of speech, legal statements in data.json unhandled
    if has_numbers(speech):

        lab_num = get_num(speech)

        if lab_num == -1:
            text_to_speech('I do not know that lab')
            write_to_json('I do not know lab' + speech, False)
            return

        temp = lab_free(lab_num)
        write_to_json(temp[0], temp[1])

    elif 'what' in speech:
        txt = what_labs_are_free()
        write_to_json(speech, txt, True)
    elif speech in POSSIBLE_INPUT:
        if lab_free():
            write_to_json(speech, "The lab is free", True)
        else:
            write_to_json(speech, "The lab is not free", True)
    else:
        text_to_speech("I don't know how to answer, try again")
        write_to_json(speech, "unhandled input")


def main():
    while True:
        if(activate_system()):
            logging.info("System Activated")
            text_to_speech("How can i help?")
            logging.info("start listing")

            # get speech
            speech = get_Speech()
            if speech == '':
                continue

            logging.info("speech understood: " + speech)

            # Process
            handle_speech(speech)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
