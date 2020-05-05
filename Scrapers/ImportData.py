#library imports
from bs4 import BeautifulSoup
import csv
import requests
import datetime

def get_year():
    	
	CurrentYear = datetime.datetime.now().year
	Currentmonth = datetime.datetime.now().month

	FirstYearBatch = CurrentYear 
	if Currentmonth>8:	
		FirstYearBatch = CurrentYear
	else:
		FirstYearBatch = CurrentYear -  1
	return FirstYearBatch

# Scrape the data from website and save it in .csv file..
def scrape_data(FirstYearBatch):
	for index, year in enumerate(["First", "Second", "Third","Fourth"]):
		
		# Access page Shreyansh's account
		page = requests.get("http://students.iitmandi.ac.in/~b17062/contacts/btech" + str(FirstYearBatch) +".php")

		#Beautiful Soup Object
		soup = BeautifulSoup(page.text , 'lxml')
		new_list=[]
		row_list=[]
		heading=[]

		table_list = soup.select('tr')	
		heading_list=table_list[8].select('h5')

		for x in heading_list:
			heading.append(x.text)

		i=0
		for contact_list in table_list[9:] :
	   		i+=1

		for j in range(9,(9+i-1)) :
			x = table_list[j].select('td')
			for y in x:
				row_list.append(y.text)
			new_list.append(row_list)
			row_list=[]
		#Writing into CSV file
		# open(str(i) + "YearBatch"+ ".csv" , 'w' ) as file
		f = csv.writer(open(str(pathlib.Path(__file__).parent.absolute()) + "/Scrapers/"   +str(year) + "YearStudent"+ ".csv", "w" ))
		# print(heading)
		f.writerow(heading)

		# print(new_list)
		for row in new_list:
			f.writerow(row)
	   

		FirstYearBatch = FirstYearBatch-  1

FirstYearBatch = get_year()
scrape_data(FirstYearBatch)
