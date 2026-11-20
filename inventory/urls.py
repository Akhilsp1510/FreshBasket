from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list_view, name='inventory_list'),
    path('restock/', views.restock_view, name='restock_general'),
    path('restock/<int:product_id>/', views.restock_view, name='restock'),
    path('reservations/', views.reservations_view, name='reservations'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
    path('log/', views.inventory_log_view, name='inventory_log'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('alerts/<int:pk>/acknowledge/', views.acknowledge_alert_view, name='acknowledge_alert'),
    path('expire-reservations/', views.expire_reservations_view, name='expire_reservations'),
]
