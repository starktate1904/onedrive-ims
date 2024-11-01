from django.db import models

#  branch model
class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)

    def delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.name

