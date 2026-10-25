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

        # Enforce notification hierarchy on both Add and Change forms
        if not self.instance.pk or self.instance.audience == 'STAFF':
            self.fields['audience'].choices = [
                ('STAFF', 'Staff'),
            ]
            self.initial['audience'] = 'STAFF'
            self.fields['audience'].help_text = (
                'Admin-created notifications are restricted to Staff / Faculty.'
            )
        else:
            # If an existing record was created for Students (via faculty interface),
            # Admin cannot change it to target another audience or bypass the hierarchy.
            self.fields['audience'].choices = [
                ('STUDENTS', 'Students'),
            ]
            self.fields['audience'].disabled = True
            self.fields['audience'].help_text = (
                'This notification targets Students and was created through '
                'the faculty interface. Admin cannot change its audience.'
            )

    def clean_audience(self):
        audience = self.cleaned_data.get('audience')

        if not self.instance.pk:
            if audience != 'STAFF':
                raise forms.ValidationError(
                    'Admin notifications can only target Staff.'
                )
            return 'STAFF'

        if self.instance.audience == 'STAFF' and audience != 'STAFF':
            raise forms.ValidationError(
                'Staff notifications cannot be changed to target Students.'
            )

        if self.instance.audience == 'STUDENTS':
            return 'STUDENTS'

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

        # Trigger push notification if the notice is published immediately
        if obj.approval_status == 'PUBLISHED' and not obj.push_sent:
            try:
                from .views import send_push_for_notification
                send_push_for_notification(obj)
            except Exception as e:
                print(f'[PUSH ERROR in Admin save_model]: {e}')


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
