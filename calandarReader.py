from datetime import time
from lxml import html
import requests
import pandas as pd

table = open('FSE Intranet - Timetable.html','r').read()
#print(tempHTMLFile)


timetable = pd.read_html(table)
timetable = timetable[0]

#Store coloumn names as they change each year
#Index 1 = Monday, Index 5 = Friday
coloumnList = timetable.columns

#for x in range (1,5):
#    print(coloumnList[x])

print(timetable[coloumnList[1]][2])

#TODO read comma seprated list