from django.urls import path
from . import views

app_name = 'products'  # Define the namespace for URL reversal

urlpatterns = [

    #  products management routes
    path('', views.product_list, name='product_list'),
    path('upload_products_csv/', views.upload_products_csv, name='upload_products_csv'),
    path('create/', views.product_create, name='product_create'),
    path('update/<int:product_id>/', views.product_update, name='product_update'),
    path('delete/<int:product_id>/', views.product_delete, name='product_delete'),
    path('restore/<int:product_id>/', views.product_restore, name='product_restore'),
]

   

    
