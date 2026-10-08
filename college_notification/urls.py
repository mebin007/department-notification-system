from django.contrib import admin
from django.urls import path
from notifications import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('departments/', views.departments, name='departments'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path(
        'notifications/',
        views.notifications,
        name='notifications'
    ),

    path(
        'login/',
        views.login,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),
]