
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

    # Home
    path('', views.home, name='home'),

    # Departments
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

    # Dashboard and notifications
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications, name='notifications'),
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

    # Authentication
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path(
        'profile/edit/',
        views.edit_profile,
        name='edit_profile',
    ),

    # Staff and student management
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

    # Attachments
    path(
        'attachments/<int:attachment_id>/download/',
        views.download_attachment,
        name='download_attachment',
    ),

    # Push notifications
    path(
        'push/subscribe/',
        views.save_push_subscription,
        name='save_push_subscription',
    ),
    path(
        'push/public-key/',
        lambda request: JsonResponse({
            'publicKey': os.environ.get('VAPID_PUBLIC_KEY', '')
        }),
        name='push_public_key',
    ),

    # Service worker
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
