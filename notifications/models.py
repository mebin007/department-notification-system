from django.db import models


class Notification(models.Model):

    title = models.CharField(max_length=200)

    department = models.CharField(max_length=150)

    description = models.TextField()

    date = models.DateField(auto_now_add=True)

    is_important = models.BooleanField(default=False)

    def __str__(self):
        return self.title