from django.contrib import admin
from .models import Notification, Profile


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
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