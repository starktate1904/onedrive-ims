from django.db import models
from auth_pos.models import User
from branches.models import Branch

# employee model
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True, default=None)
   