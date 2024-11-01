from django.contrib import admin
from .models import *


# user permissions based on roles
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 
 'email', 'role','password')
    actions = ['make_admin', 'make_manager', 'make_cashier']

    def has_view_admin_dashboard(self, user, obj=None):
        return user.is_superuser or user.role == 'admin'

    def has_view_manager_dashboard(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager'

    def has_view_cashier_dashboard(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'
    
    def has_view_user(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin' or request.user.role == 'manager'
    
    def has_create_user(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin' 


    def has_change_user(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'

    def has_delete_user(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'
 


admin.site.register(User,UserAdmin)
admin.site.register(Notification)
