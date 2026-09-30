from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Faculty', 'Faculty'),
        ('Student', 'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Student'
    )

    department = models.CharField(
        max_length=150,
        blank=True
    )

    semester = models.CharField(
        max_length=20,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Notification(models.Model):

    title = models.CharField(
        max_length=200
    )

    department = models.CharField(
        max_length=150
    )
    
    semester = models.CharField(
    max_length=20,
    blank=True
)

    description = models.TextField()

    date = models.DateField(
        auto_now_add=True
    )

    is_important = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.title