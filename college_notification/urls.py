from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
import os

from notifications import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path(
        'departments/',
        views.departments,
        name='departments',
    ),
    path(
        'departments/<int:department_id>/',
        views.department_detail,
        name='department_detail',
    ),

    path('dashboard/', views.dashboard, name='dashboard'),

    path(
        'notifications/',
        views.notifications,
        name='notifications',
    ),
    path(
        'notifications/create/',
        views.create_notification,
        name='create_notification',
    ),
    path(
        'notifications/review/',
        views.review_college_notices,
        name='review_college_notices',
    ),
    path(
        'notifications/<int:notification_id>/',
        views.notification_detail,
        name='notification_detail',
    ),

    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path(
        'staff/manage/',
        views.staff_management,
        name='staff_management',
    ),
    path(
        'students/manage/',
        views.student_management,
        name='student_management',
    ),

    path(
        'attachments/<int:attachment_id>/download/',
        views.download_attachment,
        name='download_attachment',
    ),

    path(
        'push/subscribe/',
        views.save_push_subscription,
        name='save_push_subscription',
    ),
    path(
        'push/public-key/',
        views.push_public_key,
        name='push_public_key',
    ),

    path(
        'service-worker.js',
        TemplateView.as_view(
            template_name='service-worker.js',
            content_type='application/javascript',
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )