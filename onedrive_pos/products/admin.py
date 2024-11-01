from django.contrib import admin
from .models import *




# product permissions
class ProductAdmin(admin.ModelAdmin):


    def has_view_product_list(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'

    def has_add_product(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'

    def has_update_product(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager' or user.role == 'cashier'

    def has_delete_product(self, user, obj=None):
        return user.is_superuser or user.role == 'admin' or user.role == 'manager'
    

admin.site.register(Product,ProductAdmin)
admin.site.register(Category)
    
