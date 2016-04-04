
import os
import datetime
import time
import sys

import csv

try:
    from bs4 import BeautifulSoup
except ImportError:
    print "Need Beautiful Soup to run this program"
    sys.exit()


fn = "c:/Users/Paul/Dropbox/Papers/DGY_BailEffects/Output/Records/0B02182285.html"
with open(fn, 'rb') as f:
    print "Running "
    soup = BeautifulSoup(f.read(),  "html.parser")
    for line in  soup.find_all("span", class_="FirstColumnPrompt"):
        print line.text
        data= line.parent.parent.find_all("span", class_=["Value", "Prompt"])
        data2 = [line.text.strip()] + [x.text.strip() for x in data]
        print data2


