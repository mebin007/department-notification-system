
from django.contrib import admin
from django import forms
from .models import (
    Department,
    Notification,
    Profile,
    NotificationAttachment,
    PushSubscription,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


def get_existing_departments():
    profile_departments = Profile.objects.exclude(
        department=''
    ).exclude(
        department__isnull=True
    ).values_list('department', flat=True)

    notification_departments = Notification.objects.exclude(
        department=''
    ).exclude(
        department__isnull=True
    ).values_list('department', flat=True)

    managed_departments = Department.objects.filter(
        is_active=True
    ).values_list('name', flat=True)

    return sorted(
        set(profile_departments)
        | set(notification_departments)
        | set(managed_departments),
        key=str.lower,
    )


class NotificationAdminForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = '__all__'
        widgets = {
            'department': forms.Select(choices=[]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = get_existing_departments()

        choices = [('', '---------')] + [
            (department, department)
            for department in departments
        ]

        current = self.instance.department
        if current and current not in departments:
            choices.append((current, current))

        self.fields['department'].widget.choices = choices


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm

    list_display = (
        'title',
        'department',
        'semester',
        'date',
        'is_important',
    )

    list_filter = (
        'department',
        'semester',
        'is_important',
    )

    search_fields = (
        'title',
        'description',
        'department',
        'semester',
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'department',
        'semester',
    )

    list_filter = (
        'role',
        'department',
        'semester',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
    )


@admin.register(NotificationAttachment)
class NotificationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('notification', 'file', 'uploaded_at')
    search_fields = ('notification__title',)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    search_fields = ('user__username',)
