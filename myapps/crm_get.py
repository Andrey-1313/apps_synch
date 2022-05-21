import requests
import json
import re
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Retailcrm:
	url = 'https://kilimi.retailcrm.ru/api/v5/orders/'
	headers = {'X-API-KEY':os.getenv('X-API-KEY')}
	order_items = []

	# return id and quantity of odred products
	def order_items(self, order_id):
		order_items = []
		resp = json.loads((requests.get(self.url+order_id, headers=self.headers, \
							params={'by': 'id'}).text))['order']['items']
		for i in resp:
			data = i['offer']['xmlId'], i['quantity']
			order_items.append(data)
		return order_items

	# concat previous and new comments in comment field
	def post_mcomment(self, order_id, new_comment):
		try:
			comment = json.loads((requests.get(self.url+order_id, headers=self.headers, \
									params={'by': 'id'}).text))['order']['managerComment']
			post_comment = comment + new_comment
		except KeyError:
			post_comment = new_comment
		data = json.dumps({"id": order_id,"managerComment": post_comment})
		requests.post(self.url+order_id+'/edit', data={'order':data, 'by': 'id'}, headers=self.headers)

	# change order statuse in crm
	def change_status(self, order_id, status):
		data=json.dumps({"id": order_id,"status": status})
		requests.post(self.url+order_id+'/edit', data={'order':data, 'by': 'id'}, headers=self.headers)

class Msklad_report:
    a_auth = (os.getenv('MS_Login'), os.getenv('MS_Pass'))
    url='https://online.moysklad.ru/api/remap/1.2/'
    # check if stock product qty >= required
    def get_stock(self, prod_id, required_qty):
        stock = 0
        message = ''
        data = json.loads(requests.get(self.url+'report/stock/all?filter=search='+prod_id, auth=self.a_auth).text)
        if len(data['rows']) < 1:
            availability = 0
        else:
            availability = (data['rows'][0]['quantity'])
            if availability >= required_qty:
                stock = 1
            else:
                name = re.sub(r'\s.+', '', data['rows'][0]['name'])
                message = f'на складе {int(availability)} шт {name} \n'

        return stock, message

    def check_items(self, prod_id):
    	data = json.loads(requests.get(self.url+'entity/product/?filter=externalCode='+prod_id, auth=self.a_auth).text)
    	try:
    		data['rows'][0]['meta']['href']
    	except IndexError:
    		return 'нет товара'


def return_stock(order_id):
	items = Retailcrm().order_items(order_id)
	stock = []
	# check if product exist in crm, if not - break and notify
	for xmlId, qty in items:
		stock.append(Msklad_report().get_stock(xmlId, qty))
		if Msklad_report().check_items(xmlId) == 'нет товара':
			requests.get('https://api.telegram.org/bot5051556737:'+os.getenv('telegram_api_key')+'/sendMessage', \
							params={'chat_id': '1119170661', 'text':'нет товара '+xmlId})
			break

	general_stock_statuse = 0
	message=''
	for stock_statuse, msg in stock:
		general_stock_statuse += stock_statuse
		# group not empty messages for each order position
		if 'на складе' in msg:
			message+=msg

	if len(message)>0:
		Retailcrm().post_mcomment(order_id, message)
	# if general stock status equals order products qty > change order statuse
	if len(stock) == general_stock_statuse:
		Retailcrm().change_status(order_id, 'availability-confirmed')
