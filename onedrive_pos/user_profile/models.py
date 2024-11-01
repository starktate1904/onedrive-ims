from django.db import models
from auth_pos.models import User
from staff.models import Employee



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='media/profile_pics/', blank=True, null=True)
    
   

    def __str__(self):
        return self.user.username 

