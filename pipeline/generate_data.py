from datetime import timedelta, date
import pandas as pd 
import numpy as np 
import requests

TOKEN = '0a9f5eb496bc7b1ce18c4f41fcc6948197580cb1'

def daterange(start_date, end_date):
	for n in range(int((end_date - start_date).days)):
		yield start_date + timedelta(n)

def create_url(date):
	tiingo_url = 'https://api.tiingo.com/tiingo/news?'
	url = tiingo_url+'startDate='+date+'&'+'endDate='+date+'&'+'token='+TOKEN
	return url

def get_data(start_date, end_date, headers, tickers = None):
	dates = []
	temp = []
	text = []
	for i, single_date in enumerate(daterange(start_date, end_date)):
		temp.append(single_date.strftime('%Y-%m-%d'))
		url = create_url(temp[i])
		requestResponse = requests.get(url, headers = headers)
		for i in requestResponse.json():
			print(i['publishedDate'])
			dates.append(single_date.strftime('%Y-%m-%d'))
			text.append(i['title'] + i['description'])
	return dates, text

start_date = date(2019, 8, 24)
end_date = date(2019, 8, 30)

#for i, single_date in enumerate(daterange(start_date, end_date)):
#	dates.append(single_date.strftime('%Y-%m-%d'))
#	create_url(dates[i])
	#print(single_date.strftime('%Y-%m-%d'))


headers = {'Content-Type': 'application/json'}

data = pd.DataFrame(columns=['date', 'text'])

dates, text = get_data(start_date, end_date, headers)
data['date'] = dates
data['text'] = text
print(data)