from django.urls import path
from . import views

app_name = 'branches'  # Define the namespace for URL reversal

urlpatterns = [


  #  branch management routes
    path('', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/delete/<str:id>', views.branch_delete, name='branch_delete'),
    path('branches/update/<str:id>',views.branch_update, name= "branch_update"),
    path('save_update_branch',views.save_update_branch, name= "save_update_branch"),
    path('branches/<int:branch_id>/', views.branch_detail, name='branch_detail'),
    path('branch_products/<int:branch_id>/',views.branch_products, name='branch_products'),
    path('branch_products/', views.view_branch_products, name='view_branch_products'),
    path('branch_employees/', views.view_branch_employees, name='view_branch_employees'),
    path('branch/employees/<int:employee_id>/update/',views.branch_employee_update, name='branch_employee_update'),
    path('branch/employees/<int:employee_id>/delete/', views.branch_employee_delete, name='branch_employee_delete'),

    

]