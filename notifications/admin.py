from django.contrib import admin
from django import forms
from django.utils import timezone

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


class NotificationAttachmentInline(admin.TabularInline):
    model = NotificationAttachment
    extra = 1


class NotificationAdminForm(forms.ModelForm):
    class Meta:
        model = Notification
        exclude = ('publish_at',)
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
        self.fields['department'].widget.choices = choices

        # Principal / Admin can target All Users, Students, or Staff
        self.fields['audience'].choices = [
            ('ALL', 'All Users (Students & Staff)'),
            ('STUDENTS', 'Students Only'),
            ('STAFF', 'Staff / Faculty Only'),
        ]
        self.fields['audience'].help_text = (
            'Select target audience: All Users, Students Only, or Staff/Faculty Only.'
        )

    def clean_audience(self):
        audience = self.cleaned_data.get('audience')
        if audience not in ('ALL', 'STUDENTS', 'STAFF'):
            raise forms.ValidationError('Please choose a valid audience: All Users, Students, or Staff.')
        return audience


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm
    inlines = [NotificationAttachmentInline]

    list_display = (
        'title',
        'department',
        'semester',
        'audience',
        'approval_status',
        'date',
        'is_important',
    )

    list_filter = (
        'audience',
        'approval_status',
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

    def save_model(self, request, obj, form, change):
        if not change:
            if not obj.author:
                obj.author = request.user
            obj.publish_at = timezone.now()

        super().save_model(request, obj, form, change)

        # Trigger push notification if the notice is published
        if obj.approval_status == 'PUBLISHED':
            try:
                from .views import send_push_for_notification
                send_push_for_notification(obj)
            except Exception as e:
                print(f'[PUSH ERROR in Admin save_model]: {e}')

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if form.instance.approval_status == 'PUBLISHED' and not form.instance.push_sent:
            try:
                from .views import send_push_for_notification
                send_push_for_notification(form.instance)
            except Exception as e:
                print(f'[PUSH ERROR in Admin save_related]: {e}')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'department',
        'semester',
        'is_approved',
    )
    list_filter = (
        'role',
        'department',
        'semester',
        'is_approved',
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
