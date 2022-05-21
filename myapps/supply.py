import json
import requests
import datetime
import pandas as pd
import csv
import os
workpath = os.path.dirname(os.path.abspath(__file__))
# import jsn # local test
from kilimi.myapps import jsn
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

a_auth=(os.getenv('MS_Login'), os.getenv('MS_Pass'))

def telegram_notif(info):
	return requests.get('https://api.telegram.org/bot5051556737:'+os.getenv('telegram_api_key')\
						+'/sendMessage', params={'chat_id': '1119170661', 'text':info})

class Retailcrm:
	url='https://kilimi.retailcrm.ru/api/v5/orders/'
	headers={'X-API-KEY':os.getenv('X-API-KEY')}

	def order_items(self, order_id): # get products from RetailCrm
		order_items=[]
		resp = json.loads((requests.get(self.url+order_id, headers=self.headers, params={'by': 'id'}).text))['order']['items']
		for i in resp:
			data=i['offer']['xmlId'], i['quantity']
			order_items.append(data)
		return order_items

	def order_msklad(self, order_id): # check if the order is synchronized into MoySklad
		try:
			msklad_order_id = json.loads((requests.get(self.url+order_id, headers=self.headers, \
											params={'by': 'id'}).text))['order']['customFields']['moyskladexternalid']
		except KeyError:
			order_date=json.loads((requests.get(self.url+order_id, headers=self.headers, params={'by': 'id'}).text))['order']['createdAt']
			if (datetime.datetime.now()-pd.to_datetime(order_date)).total_seconds()/60<30:
				msklad_order_id = 'new'
			else:
				telegram_notif('Не выгрузился заказ '+order_id)
				msklad_order_id = 'none'

		return msklad_order_id

	def order_supplier(self, order_id): # get supplier, if it defined in order
		try:
			supplier = json.loads((requests.get(self.url+order_id, headers=self.headers, \
									params={'by': 'id'}).text))['order']['customFields']['supplier_list_field']
		except KeyError:
			supplier = 'none'
		return supplier

	def get_item_supplier(self, xmlId): # get supplier for certain product 
		url='https://kilimi.retailcrm.ru/api/v5/store/products'
		try:
			supplier = json.loads((requests.get(url, headers=self.headers, \
									params={'filter[xmlId]': xmlId}).text))['products'][0]['offers'][0]['properties']['supplier']
		except KeyError:
			supplier = 'none'
		return supplier


class Msklad_report:
    a_auth=(os.getenv('MS_Login'), os.getenv('MS_Pass'))
    url='https://online.moysklad.ru/api/remap/1.2/'

    def get_positions(self, order_exid): # return dict - product link : reserve status  
    	ord_products={}
    	data = json.loads(requests.get(self.url+'entity/customerorder/'+order_exid+'/positions', auth=self.a_auth).text)['rows']
    	for i in data:
    		ord_products[i['assortment']['meta']['href']]=i['reserve']
    	return ord_products

    def get_stock(self, prod_id, qty): # return overall item stock qty
        data = json.loads(requests.get(self.url+'report/stock/all?filter=search='+prod_id, auth=self.a_auth).text)
        if len(data['rows'])<1:
            availability=0
        else:
            availability=(data['rows'][0]['quantity'])
        return availability

    def check_items(self, prod_id): # check if product exists in MS database
    	data = json.loads(requests.get(self.url+'entity/product/?filter=externalCode='+prod_id, auth=self.a_auth).text)
    	try:
    		return data['rows'][0]['meta']['href']
    	except IndexError:
    		telegram_notif('Нет товара в мс '+prod_id)

    def check_define_supply(self, supplier): # check if supply document from current supplier were created today 
    	try:
    		date=str(datetime.datetime.now())[:10]
    		supply_pos = json.loads(requests.get(self.url+'entity/supply?filter=moment>'+date\
    											+' 07:00:00;applicable=false;agent='+supplier, \
    											auth=self.a_auth).text)['rows'][0]['positions']['meta']['href']
    		return supply_pos
    	except IndexError:
    		supply_pos = None
    		return supply_pos


def add_supplier(name): # rerurn tuple - (internal code (link) in MS; supplier currency )
	with open(workpath+'/suppliers_list.csv', 'r', encoding='UTF8') as file:
	  reader2 = csv.reader(file)
	  for row in reader2:
	  	if name in row:
	  		return row[1], row[3]  


def main_create(order_id):
	try: # will work if order has been synchronized into MS 
	# create ms dict with items, reserved in mysklad
		ms_prod_links_dict=Msklad_report().get_positions(Retailcrm().order_msklad(order_id))

	# create crm list prod link from ms
		retail_ms_prod_links=[]
		for item_id, qty in Retailcrm().order_items(order_id):
			needed_data=item_id, qty, Msklad_report().check_items(item_id)
			retail_ms_prod_links.append(needed_data)

	# check if prod from crm in ms
		for item_id, qty, link in retail_ms_prod_links:
			if link not in ms_prod_links_dict:
				telegram_notif('Проверить товары мс в заказе  '+order_id)

	# check stock and append products list
		after_st_retail_ms_prod_links=[] # list of required product exclusive of stock inventory
		for item_id, qty, link in retail_ms_prod_links:
			qty=qty-Msklad_report().get_stock(item_id, qty)
			try:
				qty=qty-ms_prod_links_dict.get(link)
			except TypeError:
				pass
			if qty>0:
				data=item_id, qty, link
				after_st_retail_ms_prod_links.append(data)

	# consider reserved items
		# for item_id, qty, link in after_st_retail_ms_prod_links:
		# 	qty=qty-ms_prod_links_dict.get(link)
		# 	print(ms_prod_links_dict.get(link), qty)
		# 	if qty>0:
		# 		data=item_id, qty, link
		# 		after_st_retail_ms_prod_links.append(data)
		# print (after_st_retail_ms_prod_links)

	except KeyError: # if order has NOT synchronized into MS
		telegram_notif('Except order '+order_id)

	# create crm list prod link from ms
		retail_ms_prod_links=[]
		for item_id, qty in Retailcrm().order_items(order_id):
			needed_data=item_id, qty, Msklad_report().check_items(item_id)
			retail_ms_prod_links.append(needed_data)

	#check stock and append new list with nessesary items
		after_st_retail_ms_prod_links=[]
		for item_id, qty, link in retail_ms_prod_links:
			qty=qty-Msklad_report().get_stock(item_id, qty)
			if qty>0:
				data=item_id, qty, link
				after_st_retail_ms_prod_links.append(data)

	with_supplier=[] #list if required products grouped by supplier
	if len(after_st_retail_ms_prod_links)>0:
		# if supplier defined for order itself
		if Retailcrm().order_supplier(order_id) != 'none' and Retailcrm().order_supplier(order_id) != 'multi':
			supplier_code = Retailcrm().order_supplier(order_id)

			for xmlid, qty, link in after_st_retail_ms_prod_links:
				data = xmlid, qty, link, supplier_code, add_supplier(supplier_code)[0], add_supplier(supplier_code)[1]
				with_supplier.append(data)
		else: #check if supplier specified for each product or call it Noname
			for xmlid, qty, link in after_st_retail_ms_prod_links:
				data = xmlid, qty, link, Retailcrm().get_item_supplier(xmlid), add_supplier(Retailcrm().get_item_supplier(xmlid))[0], add_supplier(Retailcrm().get_item_supplier(xmlid))[1]
				with_supplier.append(data)


	for xmlid, qty, prod_link, supl_name, supl_link, currency in with_supplier:
		# if supply created - add product
		if Msklad_report().check_define_supply(supl_link) != None:
			resp = requests.post(Msklad_report().check_define_supply(supl_link), json=jsn.one_position(qty, 100, prod_link), auth=a_auth)
			if resp.reason != 'OK':
				telegram_notif('Ошибка приемки, товар '+xmlid+' ,заказ '+order_id)
		else: # create new supply document 
			resp=requests.post('https://online.moysklad.ru/api/remap/1.2/entity/supply', json=jsn.create_supply(qty, 100, prod_link, currency, supl_link), auth=a_auth)
			if resp.reason != 'OK':
				telegram_notif('Ошибка приемки, товар '+xmlid+' ,заказ '+order_id)
	return resp.reason
