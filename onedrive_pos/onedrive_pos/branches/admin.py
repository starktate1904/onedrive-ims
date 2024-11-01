from django.contrib import admin
from .models import Branch 


# branch permissions
class BranchAdmin(admin.ModelAdmin):
    list_display = ('location', 'name')

    def has_view_branch_list(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'

    def has_add_branch(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'

    def has_update_branch(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager'

    def has_delete_branch(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager'
    



admin.site.register(Branch,BranchAdmin)