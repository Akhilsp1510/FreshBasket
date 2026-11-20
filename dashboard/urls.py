from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home_view, name='home'),
    path('products/', views.product_management_view, name='product_management'),
    path('products/add/', views.add_product_view, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product_view, name='edit_product'),
    path('products/<int:pk>/toggle/', views.toggle_product_view, name='toggle_product'),
    path('categories/', views.category_management_view, name='category_management'),
    path('categories/<int:pk>/edit/', views.edit_category_view, name='edit_category'),
]

