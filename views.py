from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from kilimi.myapps import crm_get
from kilimi.myapps import supply
import json
import requests


class OrderView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, order_id):
        crm_get.return_stock(order_id)
        return Response()

class SupplyView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        data=supply.main_create(request.POST["order_id"])
        return Response(data)