
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Principal / Admin'),
        ('Faculty', 'Staff / Teacher'),
        ('Student', 'Student'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='Student'
    )
    department = models.CharField(max_length=150, blank=True)
    semester = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_profiles'
    )

    def __str__(self):
        return f'{self.user.username} - {self.role}'


class Notification(models.Model):
    APPROVAL_CHOICES = [
        ('PUBLISHED', 'Published'),
        ('PENDING', 'Awaiting principal approval'),
    ]
    AUDIENCE_CHOICES = [
        ('ALL', 'All Users (Students & Staff)'),
        ('STUDENTS', 'Students'),
        ('STAFF', 'Staff / Faculty'),
    ]

    title = models.CharField(max_length=200)
    department = models.CharField(max_length=150, blank=True)
    semester = models.CharField(max_length=20, blank=True)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    is_important = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_college_wide = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    audience = models.CharField(
        max_length=10, choices=AUDIENCE_CHOICES, default='ALL'
    )
    approval_status = models.CharField(
        max_length=12, choices=APPROVAL_CHOICES, default='PUBLISHED'
    )
    publish_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dnms_notifications'
    )
    related_links = models.JSONField(
        default=list, blank=True,
        help_text='List of {label, url} objects'
    )
    contact_name = models.CharField(max_length=150, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return self.title

    @property
    def is_visible_now(self):
        return (
            self.approval_status == 'PUBLISHED'
            and self.publish_at <= timezone.now()
        )


class NotificationAttachment(models.Model):
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(upload_to='notice_pdfs/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class PushSubscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Push subscription for {self.user.username}'
