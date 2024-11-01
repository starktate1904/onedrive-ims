from django.urls import path
from . import views

app_name = 'staffs'

urlpatterns = [


    #  employee management routes
    path('', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/update/',views.employee_update, name='employee_update'),
    path('employees/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    


   
    
]