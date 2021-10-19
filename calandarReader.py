from datetime import datetime, time
from lxml import html
from numpy import empty
#import requests
import pandas as pd

LOCATION = 'CF104'

class lab:
    name: str
    duration: str
    location = []

    def __init__(self,name,duration,location) -> None:
        self.name = name
        self.duration = duration
        if ',' in location:
            self.location = location.split(',')
        else:
            self.location.append(location)
    
    def __str__(self) -> str:
        return 'Module:\t\t' + self.name + '\n'+ 'Duration:\t' + self.duration +'\n' + 'Location:\t' + str(self.location)



timetable = pd.read_html(open('FSE Intranet - Timetable.html', 'r').read())
timetable = timetable[0]
timetable.to_csv('timetable')
# Store coloumn names as they change each week
# index 0 of coloumns is not needed 
coloumnList = timetable.columns[1:5]



#Reads Line of table and turns all labs in said slot into objects stored in a list
commaLine = str(timetable[coloumnList[3]][0]).split('CS')
listOfLabs = []
for item in commaLine:
    x = item.split('  ')
    x = list(filter(None,x))
    if not x :
        del x
    else:
        if len(x) == 4:
            listOfLabs.append(lab('CS' + x[0],x[2],x[3]))
        elif len(x) == 3:
            listOfLabs.append(lab('CS' + x[0],x[1],x[2]))



def getLabSlot():
    day = int(datetime.now().strftime('%u'))
    hour = int(datetime.now().strftime('%H'))
    
    #If it's the weekend or it's before 9am and after 6pm
    if day > 4 or hour > 18 or hour < 9:
        return []

    commaLine = str(timetable[getColoumnName(day)][getRow(hour)]).split('CS')
    listOfLabs = []
    for item in commaLine:
        x = item.split('  ')
        x = list(filter(None,x))
        if len(x) == 4:
           listOfLabs.append(lab('CS' + x[0],x[2],x[3]))
        elif len(x) == 3:
            listOfLabs.append(lab('CS' + x[0],x[1],x[2]))

    return listOfLabs

def getColoumnName(num) -> str:
    return coloumnList[num-1]

def getRow(num) -> int:
    #9am == 0
    #5pm == 8
    return num - 9

for x in getLabSlot():
    print(x)