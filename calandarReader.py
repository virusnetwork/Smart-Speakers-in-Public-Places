from datetime import time
from lxml import html
from numpy import empty
import requests
import pandas as pd

class lab:
    name: str
    duration: str
    location: str

    def __init__(self,name,duration,location) -> None:
        self.name = name
        self.duration = duration
        self.location = location
    
    def __str__(self) -> str:
        return 'Module:    ' + self.name + '\n'+ 'Duration:   ' + self.duration +'\n' + 'Location:     ' + self.location


def getDat(num: int) -> str:
    match num:
        case 1:
            return ''

table = open('FSE Intranet - Timetable.html', 'r').read()
# print(tempHTMLFile)



timetable = pd.read_html(table)
timetable = timetable[0]
# Store coloumn names as they change each year
# Index 1 = Monday, Index 5 = Friday
coloumnList = timetable.columns
for x in coloumnList:
    print(x)

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