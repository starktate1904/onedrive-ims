from django.db import models
from products.models import Product
from staff.models import Employee
from branches.models import Branch
from django.db.models import Count

class ValidSaleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            total_items=Count('saleitem')
        ).filter(
            total_items__gt=0,
            total_amount__gt=0
        )



class Sale(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    cashier = models.ForeignKey(Employee, on_delete=models.CASCADE,null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    objects = ValidSaleManager()
    all_objects = models.Manager()
  

    def __str__(self):
        return f'Sale {self.id}' 


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product ,related_name='sale_items', on_delete=models.CASCADE)
    quantity = models.IntegerField()
      # Assuming quantity is always positive
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)







