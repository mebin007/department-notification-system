from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Notification


def home(request):
    return render(request, 'home.html')


def departments(request):
    return render(request, 'departments.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


@login_required
def notifications(request):

    if request.user.is_authenticated:

        try:
            profile = request.user.profile

            all_notifications = Notification.objects.filter(
                department=profile.department
            ).filter(
                Q(semester=profile.semester) |
                Q(semester='')
            ).order_by('-date')

        except Exception:
            all_notifications = Notification.objects.none()

    else:
        all_notifications = Notification.objects.all().order_by('-date')

    return render(
        request,
        'notifications.html',
        {'notifications': all_notifications}
    )


def login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            auth_login(request, user)
            return redirect('/dashboard/')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')