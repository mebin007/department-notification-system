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

        # Make related_links user-friendly: accept plain URLs
        if 'related_links' in self.fields:
            self.fields['related_links'].required = False
            self.fields['related_links'].help_text = (
                'Paste one or more URLs (one per line). '
                'They will be auto-converted to the required format.'
            )
            self.fields['related_links'].widget = forms.Textarea(attrs={
                'rows': 3,
                'cols': 80,
                'placeholder': 'https://example.com/form\nhttps://example.com/doc',
            })

    def clean_audience(self):
        audience = self.cleaned_data.get('audience')
        if audience not in ('ALL', 'STUDENTS', 'STAFF'):
            raise forms.ValidationError('Please choose a valid audience: All Users, Students, or Staff.')
        return audience

    def clean_related_links(self):
        """Auto-convert plain URLs or comma-separated URLs into proper JSON list.

        Accepts:
          - A valid JSON list of {label, url} objects (pass-through)
          - A single URL string  → [{"label": "Link", "url": "<value>"}]
          - Multiple URLs (one per line or comma-separated)
          - Empty / blank → []
        """
        import json
        import re

        raw = self.cleaned_data.get('related_links')

        # Already a list (JSONField successfully parsed it)
        if isinstance(raw, list):
            return raw

        # None or empty
        if raw is None:
            return []

        # If it's a string, try to handle it
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return []

            # Try parsing as JSON first
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return [parsed]
            except (json.JSONDecodeError, ValueError):
                pass

            # Not valid JSON – treat as plain URL(s)
            # Split by newlines, commas, or spaces
            url_pattern = re.compile(r'https?://\S+')
            urls = url_pattern.findall(raw)

            if urls:
                return [{"label": f"Link {i+1}" if len(urls) > 1 else "Link", "url": u} for i, u in enumerate(urls)]

            # Fallback: treat entire string as a single URL/text
            return [{"label": "Link", "url": raw}]

        return raw if raw else []


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
