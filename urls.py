from django.urls import include, path
from . import views


urlpatterns = [
    path('api/<slug:order_id>', views.OrderView.as_view(), name='order'),
    path('api/supply/', views.SupplyView.as_view(), name='supply'),
]