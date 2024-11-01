
from django.urls import path
from . import views
app_name = 'auth_pos'  # Define the namespace for URL reversal


urlpatterns = [
    #  authentication routes
    path('register/', views.register, name='register'),
    path('', views.login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('lock_screen/', views.lock_screen, name='lock_screen'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('manager_dashboard', views.manager_dashboard, name='manager_dashboard'),
    path('cashier_dashboard', views.cashier_dashboard, name='cashier_dashboard'),
    path('sales/', views.admin_sale_list, name='admin_sale_list'),
    path('branch/sales/', views.manager_sales_list_view, name='manager_sale_list'),
    path('notifications/mark-as-read/<int:notification_id>/',views.mark_as_read, name='mark_as_read'),
]