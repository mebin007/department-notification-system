from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Notification, Profile


def home(request):
    return render(request, 'home.html')


def departments(request):
    return render(request, 'departments.html')


@login_required
def dashboard(request):

    try:
        profile = request.user.profile

        department = profile.department
        semester = profile.semester

        department_notifications = Notification.objects.filter(
            department=department
        ).filter(
            Q(semester=semester) |
            Q(semester='')
        )

        total_notifications = department_notifications.count()

        important_notifications = department_notifications.filter(
            is_important=True
        ).count()

    except Profile.DoesNotExist:

        department = ''
        semester = ''
        total_notifications = 0
        important_notifications = 0

    return render(
        request,
        'dashboard.html',
        {
            'department': department,
            'semester': semester,
            'total_notifications': total_notifications,
            'important_notifications': important_notifications,
        }
    )


@login_required
def notifications(request):

    try:
        profile = request.user.profile

        search_query = request.GET.get('search', '').strip()

        all_notifications = Notification.objects.filter(
            department=profile.department
        ).filter(
            Q(semester=profile.semester) |
            Q(semester='')
        )

        if search_query:
            all_notifications = all_notifications.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(department__icontains=search_query) |
                Q(semester__icontains=search_query)
            )

        all_notifications = all_notifications.order_by('-date')

    except Exception:

        all_notifications = Notification.objects.none()
        search_query = ''

    return render(
        request,
        'notifications.html',
        {
            'notifications': all_notifications,
            'search_query': search_query,
        }
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


def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        department = request.POST.get('department')
        semester = request.POST.get('semester')

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return render(
                request,
                'register.html'
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        Profile.objects.create(
            user=user,
            role='Student',
            department=department,
            semester=semester
        )

        messages.success(
            request,
            'Account created successfully. Please login.'
        )

        return redirect('/login/')

    return render(
        request,
        'register.html'
    )


@login_required
def profile(request):

    try:

        user_profile = request.user.profile

    except Profile.DoesNotExist:

        user_profile = Profile.objects.create(
            user=request.user,
            role='Student'
        )

    return render(
        request,
        'profile.html',
        {
            'profile': user_profile
        }
    )


@login_required
def edit_profile(request):

    try:

        user_profile = request.user.profile

    except Profile.DoesNotExist:

        user_profile = Profile.objects.create(
            user=request.user,
            role='Student'
        )

    if request.method == 'POST':

        department = request.POST.get('department')
        semester = request.POST.get('semester')

        user_profile.department = department
        user_profile.semester = semester

        user_profile.save()

        messages.success(
            request,
            'Profile updated successfully.'
        )

        return redirect('/profile/')

    return render(
        request,
        'edit_profile.html',
        {
            'profile': user_profile
        }
    )