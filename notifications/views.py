import json
import os
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .models import (
    Department,
    Notification,
    Profile,
    NotificationAttachment,
    PushSubscription,
)

SEMESTERS = ['1', '2', '3', '4', '5', '6', '7', '8']


def get_department_names():
    return list(
        Department.objects.filter(is_active=True)
        .order_by('name')
        .values_list('name', flat=True)
    )


def role_of(user):
    if user.is_superuser:
        return 'Admin'
    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return ''


def require_roles(*roles):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if role_of(request.user) not in roles:
                return HttpResponseForbidden(
                    'You do not have permission to access this page.'
                )

            try:
                profile = request.user.profile
                if profile.role == 'Student' and not profile.is_approved:
                    return HttpResponseForbidden(
                        'Your account is awaiting approval.'
                    )
            except Profile.DoesNotExist:
                return HttpResponseForbidden(
                    'Your account has no DNMS profile.'
                )

            return view(request, *args, **kwargs)
        return wrapped
    return deco


def home(request):
    return render(request, 'home.html')


def departments(request):
    department_list = Department.objects.filter(
        is_active=True
    ).order_by('name')

    return render(
        request,
        'departments.html',
        {'departments': department_list},
    )


def department_detail(request, department_id):
    department = get_object_or_404(
        Department,
        pk=department_id,
        is_active=True,
    )

    return render(
        request,
        'department_detail.html',
        {'department': department},
    )


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        inactive_user = User.objects.filter(
            username=username,
            is_active=False,
        ).first()

        if inactive_user and inactive_user.check_password(password):
            try:
                if not inactive_user.profile.is_approved:
                    messages.info(
                        request,
                        'Your registration is pending approval by the '
                        'principal or a teacher in your department.',
                    )
                    return render(request, 'login.html')
            except Profile.DoesNotExist:
                pass

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            try:
                profile = user.profile
                if not profile.is_approved:
                    messages.error(
                        request,
                        'Your account is awaiting approval by the '
                        'principal or your department teacher.',
                    )
                    return render(request, 'login.html')
            except Profile.DoesNotExist:
                if not user.is_superuser:
                    messages.error(
                        request,
                        'Your account is not configured for DNMS. '
                        'Please contact the administrator.',
                    )
                    return render(request, 'login.html')

            auth_login(request, user)
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


def register(request):
    departments = get_department_names()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        department = request.POST.get('department', '').strip()
        semester = request.POST.get('semester', '').strip()

        if (
            not username
            or not password
            or department not in departments
            or semester not in SEMESTERS
        ):
            messages.error(
                request,
                'Please provide a username, password, department and semester.',
            )
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_active=False,
            )
            Profile.objects.create(
                user=user,
                role='Student',
                department=department,
                semester=semester,
                is_approved=False,
            )
            messages.success(
                request,
                'Registration submitted. You can log in after your '
                'principal or department teacher approves your account.',
            )
            return redirect('login')

    return render(
        request,
        'register.html',
        {
            'departments': departments,
            'semesters': SEMESTERS,
        },
    )


@require_roles('Admin', 'Faculty', 'Student')
def dashboard(request):
    profile = request.user.profile
    role = role_of(request.user)

    visible = Notification.objects.filter(
        approval_status='PUBLISHED',
        publish_at__lte=timezone.now(),
    )

    if role == 'Student':
        visible = visible.filter(
            audience='STUDENTS',
        ).filter(
            Q(is_college_wide=True)
            | Q(
                department=profile.department,
                semester__in=[profile.semester, ''],
            )
        )

    elif role == 'Faculty':
        visible = visible.filter(
            Q(audience='STAFF', is_college_wide=True)
            | Q(audience='STAFF', department=profile.department)
            | Q(audience='STUDENTS', is_college_wide=True)
            | Q(
                audience='STUDENTS',
                department=profile.department,
                semester__in=[profile.semester, ''],
            )
        )

    return render(
        request,
        'dashboard.html',
        {
            'department': profile.department,
            'semester': profile.semester,
            'total_notifications': visible.count(),
            'important_notifications': visible.filter(
                is_important=True
            ).count(),
            'role': role,
        },
    )


@require_roles('Admin', 'Faculty', 'Student')
def notifications(request):
    profile = request.user.profile
    role = role_of(request.user)
    search_query = request.GET.get('search', '').strip()

    qs = Notification.objects.filter(
        approval_status='PUBLISHED',
        publish_at__lte=timezone.now(),
    )

    if role == 'Student':
        qs = qs.filter(
            audience='STUDENTS',
        ).filter(
            Q(is_college_wide=True)
            | Q(
                department=profile.department,
                semester__in=[profile.semester, ''],
            )
        )

    elif role == 'Faculty':
        qs = qs.filter(
            Q(audience='STAFF', is_college_wide=True)
            | Q(audience='STAFF', department=profile.department)
            | Q(audience='STUDENTS', is_college_wide=True)
            | Q(
                audience='STUDENTS',
                department=profile.department,
                semester__in=[profile.semester, ''],
            )
        )

    if search_query:
        qs = qs.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(department__icontains=search_query)
        )

    return render(
        request,
        'notifications.html',
        {
            'notifications': qs.order_by(
                '-is_pinned',
                '-is_important',
                '-publish_at',
            ),
            'search_query': search_query,
            'role': role,
        },
    )


@require_roles('Admin')
def staff_management(request):
    departments = get_department_names()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        department = request.POST.get('department', '')

        if (
            not username
            or len(password) < 8
            or department not in departments
        ):
            messages.error(
                request,
                'Enter a username, password of at least 8 characters '
                'and a valid department.',
            )
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'That username already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_active=True,
            )
            Profile.objects.create(
                user=user,
                role='Faculty',
                department=department,
                is_approved=True,
                created_by=request.user,
            )
            messages.success(
                request,
                f'Staff account created for {username}.',
            )
            return redirect('staff_management')

    staff = Profile.objects.filter(
        role='Faculty'
    ).select_related('user').order_by(
        'department',
        'user__username',
    )

    return render(
        request,
        'staff_management.html',
        {
            'staff': staff,
            'departments': departments,
        },
    )


@require_roles('Admin', 'Faculty')
def student_management(request):
    role = role_of(request.user)
    profile = request.user.profile
    departments = get_department_names()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            student = get_object_or_404(
                Profile,
                pk=request.POST.get('profile_id'),
                role='Student',
            )

            if role != 'Admin' and student.department != profile.department:
                return HttpResponseForbidden(
                    'You cannot approve a student outside your department.'
                )

            student.is_approved = True
            student.user.is_active = True
            student.user.save(update_fields=['is_active'])
            student.save(update_fields=['is_approved'])

            messages.success(
                request,
                f'Approved student {student.user.username}.',
            )

        elif action == 'create':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            department = (
                request.POST.get('department', '')
                if role == 'Admin'
                else profile.department
            )
            semester = request.POST.get('semester', '')

            if (
                not username
                or len(password) < 8
                or department not in departments
                or semester not in SEMESTERS
            ):
                messages.error(
                    request,
                    'Check username, password (minimum 8 characters), '
                    'department and semester.',
                )
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'That username already exists.')
            else:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    is_active=True,
                )
                Profile.objects.create(
                    user=user,
                    role='Student',
                    department=department,
                    semester=semester,
                    is_approved=True,
                    created_by=request.user,
                )
                messages.success(
                    request,
                    f'Student account created for {username}.',
                )
                return redirect('student_management')
        else:
            return HttpResponseForbidden('Invalid action.')

    pending = Profile.objects.filter(
        role='Student',
        is_approved=False,
    ).select_related('user')

    students = Profile.objects.filter(
        role='Student',
    ).select_related('user')

    if role == 'Faculty':
        pending = pending.filter(department=profile.department)
        students = students.filter(department=profile.department)

    return render(
        request,
        'student_management.html',
        {
            'pending': pending,
            'students': students,
            'departments': departments,
            'semesters': SEMESTERS,
            'role': role,
            'my_department': profile.department,
        },
    )


@require_roles('Admin', 'Faculty')
def create_notification(request):
    role = role_of(request.user)
    profile = request.user.profile
    departments = get_department_names()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        is_college_wide = request.POST.get('is_college_wide') == 'on'

        department = (
            request.POST.get('department', '')
            if role == 'Admin'
            else profile.department
        )
        semester = request.POST.get('semester', '')

        status = (
            'PENDING'
            if role == 'Faculty' and is_college_wide
            else 'PUBLISHED'
        )

        publish_at_raw = request.POST.get('publish_at', '').strip()
        publish_at = timezone.now()

        if publish_at_raw:
            parsed = parse_datetime(publish_at_raw)
            if parsed:
                publish_at = (
                    timezone.make_aware(parsed)
                    if timezone.is_naive(parsed)
                    else parsed
                )

        if (
            not title
            or not description
            or (
                not is_college_wide
                and department not in departments
            )
        ):
            messages.error(
                request,
                'Please complete the title, description and audience.',
            )
        else:
            links = []

            for label, url in zip(
                request.POST.getlist('link_label'),
                request.POST.getlist('link_url'),
            ):
                label = label.strip()
                url = url.strip()

                if label and url and url.startswith(('https://', 'http://')):
                    links.append({
                        'label': label[:120],
                        'url': url[:1000],
                    })

            audience = 'STAFF' if role == 'Admin' else 'STUDENTS'

            notification = Notification.objects.create(
                title=title,
                description=description,
                department='' if is_college_wide else department,
                semester='' if is_college_wide else semester,
                audience=audience,
                is_important=request.POST.get('is_important') == 'on',
                is_pinned=request.POST.get('is_pinned') == 'on',
                is_college_wide=is_college_wide,
                approval_status=status,
                publish_at=publish_at,
                author=request.user,
                related_links=links,
                contact_name=request.POST.get('contact_name', '').strip(),
                contact_email=request.POST.get('contact_email', '').strip(),
                contact_phone=request.POST.get('contact_phone', '').strip(),
            )

            files = request.FILES.getlist('pdf_files')

            if len(files) > 5:
                notification.delete()
                messages.error(
                    request,
                    'Maximum 5 PDF files are allowed.',
                )
            else:
                invalid = any(
                    not file.name.lower().endswith('.pdf')
                    or file.size > 10 * 1024 * 1024
                    for file in files
                )

                if invalid:
                    notification.delete()
                    messages.error(
                        request,
                        'Only PDF files up to 10 MB each are allowed.',
                    )
                else:
                    for file in files:
                        NotificationAttachment.objects.create(
                            notification=notification,
                            file=file,
                        )

                    if status == 'PENDING':
                        messages.success(
                            request,
                            'College-wide notice submitted to the '
                            'principal for approval.',
                        )
                    else:
                        messages.success(
                            request,
                            'Notification saved. It will appear at '
                            'its publication time.',
                        )

                    if (
                        status == 'PUBLISHED'
                        and publish_at <= timezone.now()
                    ):
                        send_push_for_notification(notification)

                    return redirect('notifications')

    return render(
        request,
        'create_notification.html',
        {
            'departments': departments,
            'semesters': SEMESTERS,
            'role': role,
            'my_department': profile.department,
        },
    )


@require_roles('Admin')
def review_college_notices(request):
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification,
            pk=request.POST.get('notice_id'),
            approval_status='PENDING',
        )
        action = request.POST.get('action')

        if action == 'approve':
            notification.approval_status = 'PUBLISHED'
            notification.save(update_fields=['approval_status'])
            messages.success(
                request,
                'College-wide notice approved and published.',
            )

            if notification.publish_at <= timezone.now():
                send_push_for_notification(notification)

        elif action == 'reject':
            notification.delete()
            messages.success(request, 'Notice request rejected.')
        else:
            messages.error(request, 'Invalid action.')

        return redirect('review_college_notices')

    return render(
        request,
        'review_notices.html',
        {
            'notices': Notification.objects.filter(
                approval_status='PENDING'
            ).select_related('author').order_by('publish_at'),
        },
    )


def send_push_for_notification(notification):
    if (
        not os.environ.get('VAPID_PRIVATE_KEY')
        or not os.environ.get('VAPID_PUBLIC_KEY')
    ):
        return False

    try:
        from pywebpush import webpush
    except ImportError:
        return False

    target_role = (
        'Faculty' if notification.audience == 'STAFF' else 'Student'
    )

    subscriptions = PushSubscription.objects.select_related(
        'user',
        'user__profile',
    ).filter(
        user__profile__is_approved=True,
        user__profile__role=target_role,
    )

    if not notification.is_college_wide:
        subscriptions = subscriptions.filter(
            user__profile__department=notification.department,
        )

        if notification.audience == 'STUDENTS' and notification.semester:
            subscriptions = subscriptions.filter(
                user__profile__semester=notification.semester,
            )

    payload = json.dumps({
        'title': notification.title,
        'body': notification.description[:180],
        'url': '/notifications/',
    })

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh,
                        'auth': subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=os.environ['VAPID_PRIVATE_KEY'],
                vapid_claims={
                    'sub': os.environ.get(
                        'VAPID_SUBJECT',
                        'mailto:admin@example.com',
                    ),
                },
            )
        except Exception as exc:
            response = getattr(exc, 'response', None)
            if response is not None and response.status_code in (404, 410):
                subscription.delete()

    notification.push_sent = True
    notification.save(update_fields=['push_sent'])
    return True


@login_required
def download_attachment(request, attachment_id):
    attachment = get_object_or_404(
        NotificationAttachment.objects.select_related('notification'),
        pk=attachment_id,
    )
    notice = attachment.notification

    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return HttpResponseForbidden('No DNMS profile.')

    if profile.role == 'Student' and not profile.is_approved:
        return HttpResponseForbidden('Account awaiting approval.')

    if profile.role == 'Student':
        allowed = (
            notice.approval_status == 'PUBLISHED'
            and notice.publish_at <= timezone.now()
            and notice.audience == 'STUDENTS'
            and (
                notice.is_college_wide
                or (
                    notice.department == profile.department
                    and notice.semester in ('', profile.semester)
                )
            )
        )
    elif profile.role == 'Faculty':
        allowed = (
            notice.approval_status == 'PUBLISHED'
            and notice.publish_at <= timezone.now()
            and (
                notice.is_college_wide
                or notice.department == profile.department
            )
        )
    else:
        allowed = role_of(request.user) == 'Admin'

    if not allowed:
        return HttpResponseForbidden(
            'You are not allowed to download this attachment.'
        )

    response = FileResponse(
        attachment.file.open('rb'),
        as_attachment=True,
        filename=attachment.file.name.rsplit('/', 1)[-1],
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_POST
@require_roles('Admin', 'Faculty', 'Student')
def save_push_subscription(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        keys = data['keys']
        endpoint = data['endpoint']
    except (ValueError, KeyError, TypeError):
        return JsonResponse(
            {'ok': False, 'error': 'Invalid subscription'},
            status=400,
        )

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            'user': request.user,
            'p256dh': keys.get('p256dh', ''),
            'auth': keys.get('auth', ''),
        },
    )
    return JsonResponse({'ok': True})


@login_required
def profile(request):
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(
            user=request.user,
            role='Admin' if request.user.is_superuser else 'Student',
        )

    return render(
        request,
        'profile.html',
        {'profile': user_profile},
    )


@login_required
def edit_profile(request):
    user_profile = get_object_or_404(Profile, user=request.user)

    if user_profile.role != 'Student':
        return HttpResponseForbidden(
            'Only students can edit their academic profile.'
        )

    if request.method == 'POST':
        semester = request.POST.get('semester', '')

        if semester not in SEMESTERS:
            messages.error(request, 'Choose a valid semester.')
        else:
            user_profile.semester = semester
            user_profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

    return render(
        request,
        'edit_profile.html',
        {
            'profile': user_profile,
            'departments': get_department_names(),
            'semesters': SEMESTERS,
        },
    )