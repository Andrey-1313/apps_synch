### This app performs two main operations:
**1. Check inventory stock status** 
  [myapps/crm_get.py](myapps/crm_get.py)
- CRM sends a GET request to this app, with an order number
- The app in turn sends a request to the Inventory Platform via api
- Then app edit the order in CRM, depends on response

**2. Create supply document** 
  [myapps/supply.py](myapps/supply.py)
- The app creates or edit supply documents in Inventory Platform via api 
