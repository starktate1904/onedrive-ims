from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('create/', views.create_sale, name='create_sale'),
    path('list/', views.sale_list, name='sale_list'),
    path('view/<int:sale_id>/', views.view_sale, name='view_sale'),
    path('search-products/', views.search_products, name='search_products'),
    path('available-products', views.view_pos_products, name='view_pos_products'),
    path('add-product-to-sale/', views.add_product_to_sale, name='add_product_to_sale'),
    path('remove-product-from-sale/', views.remove_product_from_sale, name='remove_product_from_sale'),
    path('complete-sale/', views.complete_sale, name='complete_sale'),
    path('generate-report/', views.generate_sales_report, name='generate_sales_report'),
    path('branch-generate-report/', views.branch_generate_sales_report, name='branch_generate_sales_report'),
    
    
  
]