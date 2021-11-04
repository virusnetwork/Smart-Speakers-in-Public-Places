from datetime import datetime
import pandas as pd
import pyttsx3
import speech_recognition as sr
import re

LOCATION = 'Computational Foundry 104 PC'
TIMETABLE = ''
COLUMN_LIST = []


# microphone set up


def listen():
    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

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


def text_to_speech(text):
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
    global TIMETABLE
    TIMETABLE = pd.read_html(open('FSE Intranet - Timetable.html', 'r').read())
    TIMETABLE = TIMETABLE[0]
    global COLUMN_LIST
    COLUMN_LIST = TIMETABLE.columns[1:6]


# TODO: get lab slot for given times, location etc.
def get_lab_slot():
    if not TIMETABLE:
        get_timetable()

    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))
    # If it's the weekend or it's before 9am and after 6pm
    if day > 5 or hour < 9 or hour > 18:
        return []

    # noinspection PyTypeChecker
    comma_line = str(TIMETABLE[get_column_name(day)][get_row(hour)])
    print(comma_line)
    re.split('CS', comma_line)
    list_of_labs = []
    for item in comma_line:
        x = item.split('  ')
        x = list(filter(None, x))
        if len(x) == 4:
            list_of_labs.append(LabClass('CS' + x[0], x[2], x[3]))
        elif len(x) == 3:
            list_of_labs.append(LabClass('CS' + x[0], x[1], x[2]))

    return list_of_labs


def get_column_name(num):
    return COLUMN_LIST[num - 1]


def get_row(num) -> int:
    # 9am == 0
    # 5pm == 8
    return num - 9


def lab_free(location) -> bool:
    list_of_labs = get_lab_slot()
    for x in list_of_labs:
        if location in x.location:
            text_to_speech("The lab is not free")
            return False

    text_to_speech("The lab is free")
    return True


print(lab_free(LOCATION))

# TODO: added main method
