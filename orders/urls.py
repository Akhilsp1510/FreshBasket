from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_view, name='update_cart'),
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    # Customer orders
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('my-orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('my-orders/<str:order_number>/cancel/', views.cancel_order_view, name='cancel_order'),
    # Admin orders
    path('admin/orders/', views.admin_orders_view, name='admin_orders'),
    path('admin/orders/<str:order_number>/', views.admin_order_detail_view, name='admin_order_detail'),
]

