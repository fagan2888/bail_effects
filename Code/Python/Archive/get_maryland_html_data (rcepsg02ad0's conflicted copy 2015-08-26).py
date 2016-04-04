
import urllib
import os
import datetime
import time
import sys
import logging
import csv
from datetime import timedelta, date

from string import ascii_lowercase

try:
    import urllib2
    import mechanize
except ImportError:
    print "Need urllib2 and mechanize to run this program"
    sys.exit()
try:
    from bs4 import BeautifulSoup
except ImportError:
    print "Need Beautiful Soup to run this program"
    sys.exit()
    
COOKIEFILE = 'cookies.lwp'
CASE_URL = 'http://casesearch.courts.state.md.us/casesearch/'
OUTPUT_PATH = '/Users/rcepsg02/Dropbox/Papers/DGY_BailEffects/Output/Records/'
header = { 'User-Agent' : ''}

REQUEST_COUNTER = 0

print "Running: %s" % datetime.datetime.now().ctime()


logger = logging.getLogger("mechanize")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


def daterange(start_date, end_date):
    for n in range(0, int ((end_date - start_date).days), 7):
        yield start_date + timedelta(n)


def login(br):
    response=br.open('http://casesearch.courts.state.md.us/casesearch/')
    print "Logging In..."
    br.select_form("main")
    control = br.form.find_control("disclaimer")
    br.form['disclaimer'] = ['Y']
    req = br.submit()
    return br

def searchCases(br, countyList, dateStart, dateEnd, letter):
    print "Open Search Form"
    openPage(br,'http://casesearch.courts.state.md.us/casesearch/processDisclaimer.jis')
    br.select_form(nr=2)
    br.form['lastName'] = letter
    br.form['partyType'] = ['DEF']
    br.form['site'] = ['CRIMINAL']
    br.form['countyName'] = countyList
    br.form['filingStart'] = dateStart
    br.form['filingEnd'] = dateEnd
    br.submit()
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    if REQUEST_COUNTER == 100:
        time.sleep(120)
        br = login(br)
        REQUEST_COUNTER = 0
    return br

def writeSearchResults(page, output=None, br=None):
    soup = BeautifulSoup(page.read(),  "html.parser")
    results =  soup.find_all(class_ = ['odd', 'even'])
    for result in results:
        x = list(result.find_all('td'))
        url = x[0].find('a')
        line = {'caseLink' : url['href'],  'caseNum' : url.string,  'name' : x[1].string,  'dob' : x[2].string,  'partyType' : x[3].string,  'courtType' : x[4].string,  'caseType' : x[5].string,  'caseStatus' : x[6].string,  'filingDate' : x[7].string,  'caseCaption' : x[8].string}
        # except:
        #     i = 0
        #     for y in x:
        #         print i, y
        #         i = i + 1
        if output:
            output.writerow(line)
    try:
        nextLink = soup.find(text='Next').parent
    except AttributeError:
        return True
    time.sleep(1)
    page = openPage(br, nextLink['href'])
    REQUEST_COUNTER += 1
    if REQUEST_COUNTER == 100:
        time.sleep(120)
        br = login(br)
        REQUEST_COUNTER = 0
    writeSearchResults(page, output, br)

def openPage(br, link, triedTimes=2, waittime=120):
    tried = 0
    while True:
        try:
            page = br.open(link)
            return page
        except mechanize.HTTPError as e:
            print e.code
            sleep(waittime)
            br = login(br)
            tried += 1
            if tried > triedTimes:
                exit()
            continue

def searchResults(fn, page, br, overwrite=True):
    if overwrite:
        ftype = 'wb'
    else:
        ftype = 'a'
    with open(fn, ftype) as f:
        fieldnames = ['caseLink', 'caseNum', 'name', 'dob', 'partyType', 'courtType', 'caseType', 'caseStatus', 'filingDate', 'caseCaption']
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        if overwrite:
            writer.writeheader()
        writeSearchResults(page, writer, br)

def pullCourtRecord(link, caseNum, br):
    print CASE_URL + link
    page = openPage(br, CASE_URL + link)
    with open(OUTPUT_PATH + caseNum + '.html', 'wb') as f:
        f.write(page.read())
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    print REQUEST_COUNTER
    if REQUEST_COUNTER == 100:
        time.sleep(120)
        br = login(br)
        REQUEST_COUNTER = 0


def pullSearchResults(br, start_date, end_date, fn):
    startDate = start_date
    endDate = end_date
    for n in range(0, int ((end_date - start_date).days), 7):
        startDate = startDate + timedelta(n)
        endDate = startDate + timedelta(6) 
        letter = "a"
        print "Search Results for Last Name %s, between %s and %s " % ( letter, startDate.strftime("%m/%d/%Y"), endDate.strftime("%m/%d/%Y"))
        br = searchCases(br, ['BALTIMORE CITY'], startDate.strftime("%m/%d/%Y"), endDate.strftime("%m/%d/%Y"), letter )
        page = br.response()
        time.sleep(1)                    
        if n == 0:
            searchResults(fn, page, br)
        else:
            searchResults(fn, page, br, False)
        for letter in ascii_lowercase:
            if letter != "a":
                print "Search Results for Last Name %s, between %s and %s " % ( letter, startDate.strftime("%m/%d/%Y"), endDate.strftime("%m/%d/%Y"))
                br = searchCases(br, ['BALTIMORE CITY'], startDate.strftime("%m/%d/%Y"), endDate.strftime("%m/%d/%Y"), letter )
                page = br.response()
                time.sleep(1)
                searchResults(fn, page, br, False)


    
br = mechanize.Browser()
br = login(br)

# Pulling Search Results
start_date = date(2012,8,1)
end_date = date(2012,9,1)

fn = '/Users/rcepsg02/Dropbox/Papers/DGY_BailEffects/Output/searchResults.csv'

#pullSearchResults(br, start_date, end_date, fn)

# Pulling Case Records
with open(fn, 'rb') as f:
    reader = csv.DictReader(f)
    for row in reader:
        link = row['caseLink']
        caseNum = row['caseNum']
        if not os.path.isfile(OUTPUT_PATH + caseNum + '.html'):
            print "pulling Case Number %s" % caseNum
            pullCourtRecord(link, caseNum, br)
            time.sleep(1)
            print "sleeping for %d seconds..." % 5
        else:
            print "Case Number %s already exists, skipping" % caseNum
            



# List of Counties: ALLEGANY COUNTY, ANNE ARUNDEL COUNTY, BALTIMORE CITY, BALTIMORE COUNTY, CALVERT COUNTY, CAROLINE COUNTY, CARROLL COUNTY, CECIL COUNTY, CHARLES COUNTY, DORCHESTER COUNTY, FREDERICK COUNTY, GARRETT COUNTY, HARFORD COUNTY, HOWARD COUNTY, KENT COUNTY, MONTGOMERY COUNTY, PRINCE GEORGE'S COUNTY, QUEEN ANNE'S COUNTY, SAINT MARY'S COUNTY, SOMERSET COUNTY, TALBOT COUNTY, WASHINGTON COUNTY, WICOMICO COUNTY, WORCESTER COUNTY
