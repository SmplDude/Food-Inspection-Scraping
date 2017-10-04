"""
Your task is to write a python program to do the following:
    1) For each inspection for each facility on a single page of results from the Napa county health
       department website (url given below), scrape the following information:
       - Facility name
       - Address (just street info, not city, state, or zip)
       - City
       - State
       - Zipcode
       - Inspection date
       - Inspection type
       - For each out-of-compliance violation type, scrape the violation type number and corresponding description.
         For example, an inspection might contain violation type numbers 6 and 7, and descriptions
         "Adequate handwashing facilities supplied & accessible" and "Proper hot and cold holding temperatures"
    2) Place this information in a database of some sort. You can use whatever you want; sqlite, postgres, mongodb, etc.
       Organize the data in a fashion which seems the most logical and useful to you. Include in your result the
       necessary instructions to set up this database, such as create table statements.
    3) Fetch this information from the database, and print it to the console in some fashion which clearly
       and easily displays the data you scraped.

We have provided a little bit of code using the lxml and sqlite to get you started,
but feel free to use whatever method you would like.
"""



#**************************************************************************************************************************
#LUKE GREGOR
#10/2/2017
#FOOD SAFETY WEB SCRAPER
#
#
#This program was completed using python version 3.5.4 and the BeautifulSoup library
#version 4.6.0 in a windows 10 environment.
#
#
#DATABASE CONSTRUCTION:
#There are two tables in the database, one containing information about facilities,
#the other containing information on violations.
#  1. CREATE TABLE Facilities (id int, name text, address text, city text, state text, zipcode text, lastInspDate text)
#  2. CREATE TABLE Violations (id int, violNum int, description text, inspDate text, inspType text)
#
#The primary key for Facilites is the id field, while for Violations, you need id, violNum, and inspDate in order to
#identify a unique row
#**************************************************************************************************************************

from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import re
import sqlite3


page_url = (
    "http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=03/01/2017&kw1=&kw2=&kw3="
    "&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar"
)


def setup_db():
    conn = sqlite3.connect("exercise.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS Facilities (id int, name text, address text, city text, state text, zipcode text, lastInspDate text)")
    c.execute("CREATE TABLE IF NOT EXISTS Violations (id int, violNum int, description text, inspDate text, inspType text)")
    c.close()

def scrapePage(finalPage):
	conn = sqlite3.connect("exercise.db")
	c = conn.cursor()

	#collect facility info
	openstring = "http://ca.healthinspections.us/" + finalPage
	root = urlopen(openstring)
	soup = BeautifulSoup(root, "html.parser")
	topSectionList = soup.find("div", class_="topSection").find_all("span", class_="blackline")
	facilityName = topSectionList[0].text
	facilityNum = int(topSectionList[1].text)
	inspectionDate = topSectionList[2].text
	inspectionType = topSectionList[9].text
	fullAddress = topSectionList[4].text
	tempAddr, stateAndZip = fullAddress.split(',')
	address, city = tempAddr.split('\n')
	state, zipcode = stateAndZip.strip().split(' ')
	insertList = (facilityNum, facilityName, address, city, state, zipcode, inspectionDate)

	#Store in facility table
	c.execute("SELECT * FROM Facilities WHERE id=?", (facilityNum,))
	if(c.fetchall()):
		insertList = insertList + (facilityNum,)
		c.execute("UPDATE Facilities SET id=?, name=?, address=?, city=?, state=?, zipcode=?, lastInspDate=? WHERE id=?", insertList)
	else:
		c.execute("INSERT INTO Facilities VALUES (?, ?, ?, ?, ?, ?, ?)", insertList)

	#collect violation info
	tables = soup.find_all("table", class_="insideTable")
	for table in tables:
		violations = table.find_all("tr")
		for row in violations:
			rowCells = row.find_all("td")
			if(row.td and rowCells[2].img):
				if(rowCells[2].img.attrs['src'] == '../../../webadmin/dhd_135/paper/images/box_checked_10x10.gif'):
					violationLine = row.td.text
					violationNumber, violationDescription = violationLine.split('.')
					violationDescription = violationDescription.strip()

					#store in violations table
					c.execute("SELECT * FROM Violations WHERE id=? AND violNum=? AND inspDate=?", (facilityNum, violationNumber, inspectionDate))
					if not (c.fetchall()):
						tempTuple = (facilityNum, violationNumber, violationDescription, inspectionDate, inspectionType)
						c.execute("INSERT INTO Violations VALUES (?, ?, ?, ?, ?)", tempTuple)
	
	conn.commit()
	conn.close()



def intermediatePage(link):
	root = urlopen("http://ca.healthinspections.us/napa/" + link)
	soup = BeautifulSoup(root, "html.parser")
	nextPage = soup.find("a", href=re.compile("\.\.\/_templates\/135\/Food Inspection\/_report_full\.cfm\?domainID=\d+&inspectionID=\d+&dsn=dhd_\d+"))
	linkstring = nextPage.attrs["href"][3:22] + "%20"
	linkstring = linkstring + nextPage.attrs["href"][23:]
	scrapePage(linkstring)


def scrape():
    root = urlopen(page_url)
    soup = BeautifulSoup(root, "html.parser")
    search_links = soup.find_all("a", href=re.compile("estab\.cfm\?permitID=\d+&inspectionID=\d+"))  # Find all links on page
    for link in search_links:
    	intermediatePage(link.attrs["href"])


def runInterface():
	conn = sqlite3.connect("exercise.db")
	c = conn.cursor()
	print()
	print("Here is all the data I scraped from:  \n", page_url)
	print()

	c.execute("SELECT * FROM Facilities")
	print("FACILITIES: ", '\n')
	facilityInfo = c.fetchall()
	c.execute("SELECT * FROM Violations")
	violationsInfo = c.fetchall()
	for row in facilityInfo:
		print()
		print("FACILITY NUMBER: ", row[0])
		print("FACILITY NAME: ", row[1])
		print("ADDRESS: ", row[2])
		print("CITY: ", row[3])
		print("STATE: ", row[4])
		print("ZIPCODE: ", row[5])
		print("LAST DATE OF INSPECTION: ", row[6])
		found = False
		for entry in violationsInfo:
			if(entry[0] == row[0]):
				found = True
				print("VIOLATION: ", entry[1], ". ", entry[2], " DATE: ", entry[3])
		if not found:
			print("NO VIOLATIONS ON RECORD")
		print()
	conn.close()


def main():
    setup_db()
    scrape()
    runInterface()


if __name__ == '__main__':
    main()
