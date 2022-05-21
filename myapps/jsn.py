import csv
import os
workpath = os.path.dirname(os.path.abspath(__file__))


def get_currency(cur_name): # return currency code
  with open(workpath+'/currencys.csv', 'r', encoding='UTF8') as file:
    reader2 = csv.reader(file)
    for row in reader2:
      if cur_name in row:
        cur_href=row[1]

  currency={
      "currency": {
        "meta": {
          "href": cur_href,
          "type": "currency",
        }
      }
    }
  return currency



def one_position(qty, price, prod_link):
  pos=[{ "quantity": qty,
      "price": price,
      "assortment": {
        "meta": {
          "href": prod_link,
          "type": "product",
        }
      }}]
  return pos

def create_supply(qty, price, prod_link, currency_name, agent_href):
  js_supply= {
    "description" : 'змінити ціну',
    "applicable": False,
    "rate": get_currency(currency_name),
    "store": {
      "meta": {
        "href": "https://online.moysklad.ru/api/remap/1.2/entity/store/a04fa169-5103-11ec-0a80-08bb00249c2b",
        "type": "store",
      }
    },
    "agent": {
      "meta": {
        "href": agent_href,
        "type": "counterparty",
      }
    },
    "organization": {
      "meta": {
        "href": "https://online.moysklad.ru/api/remap/1.2/entity/organization/a04e5a14-5103-11ec-0a80-08bb00249c29",
        "type": "organization",
      }
    },
    "positions": one_position(qty, price, prod_link)
    }
  return js_supply

