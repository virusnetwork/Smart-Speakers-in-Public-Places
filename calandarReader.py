from datetime import datetime, time
from lxml import html
from numpy import empty
#import requests
import pandas as pd

LOCATION = 'CF104'
TIMETABLE = ''
COLOUMN_LIST = []


class lab:
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
        return 'Module:\t\t' + self.name + '\n' + 'Duration:\t' + self.duration + '\n' + 'Location:\t' + str(self.location)


# Store coloumn names as they change each week
# index 0 of coloumns is not needed


def getTimetable():
    # TODO: get timetable from website
    # try website if not use html
    global TIMETABLE
    TIMETABLE = pd.read_html(open('FSE Intranet - Timetable.html', 'r').read())
    TIMETABLE = TIMETABLE[0]
    global COLOUMN_LIST
    COLOUMN_LIST = TIMETABLE.columns[1:5]


# TODO: get lab slot for given times, location etc.
def getLabSlot():
    if not TIMETABLE:
        getTimetable()

    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))

    # If it's the weekend or it's before 9am and after 6pm
    if day > 4 or hour > 18 or hour < 9:
        return []

    commaLine = str(TIMETABLE[getColoumnName(day)][getRow(hour)]).split('CS')
    listOfLabs = []
    for item in commaLine:
        x = item.split('  ')
        x = list(filter(None, x))
        if len(x) == 4:
            listOfLabs.append(lab('CS' + x[0], x[2], x[3]))
        elif len(x) == 3:
            listOfLabs.append(lab('CS' + x[0], x[1], x[2]))

    return listOfLabs


def getColoumnName(num) -> str:
    return COLOUMN_LIST[num-1]


def getRow(num) -> int:
    # 9am == 0
    # 5pm == 8
    return num - 9


for x in getLabSlot():
    print(x)

# TODO: added main method
