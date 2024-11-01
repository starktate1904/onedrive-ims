from django.contrib import admin
from .models import *


# employee permissions
class EmployeeAdmin(admin.ModelAdmin):


    def has_view_employee_list(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager'

    def has_add_employee(self, user, obj=None):
        return user.is_superuser or user.role == 'admin'

    def has_update_employee(self, user, obj=None):
        return user.is_superuser or user.role == 'admin'

    def has_delete_employee(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' 
    

admin.site.register(Employee,EmployeeAdmin)
