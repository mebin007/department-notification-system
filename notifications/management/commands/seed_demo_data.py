import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from notifications.models import Profile, Notification


class Command(BaseCommand):
    help = "Create demo users, profiles, and notifications for DNMS."

    def handle(self, *args, **options):

        student_password = os.environ.get("DEMO_STUDENT_PASSWORD")
        admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")

        if not student_password or not admin_password:
            raise RuntimeError(
                "DEMO_STUDENT_PASSWORD and DEMO_ADMIN_PASSWORD "
                "must be set in the environment."
            )

        # -------------------------
        # Student account
        # -------------------------

        student, student_created = User.objects.get_or_create(
            username="student1"
        )

        student.first_name = "Student"
        student.last_name = "One"
        student.email = "student1@dnms.demo"

        if student_created:
            student.set_password(student_password)

        student.save()

        Profile.objects.update_or_create(
            user=student,
            defaults={
                "role": "Student",
                "department": "Computer Applications",
                "semester": "5",
            },
        )

        # -------------------------
        # Admin account
        # -------------------------

        admin, admin_created = User.objects.get_or_create(
            username="admindnms"
        )

        admin.first_name = "DNMS"
        admin.last_name = "Administrator"
        admin.email = "admin@dnms.demo"
        admin.is_staff = True
        admin.is_superuser = True

        if admin_created:
            admin.set_password(admin_password)

        admin.save()

        Profile.objects.update_or_create(
            user=admin,
            defaults={
                "role": "Admin",
                "department": "",
                "semester": "",
            },
        )

        # -------------------------
        # Notifications
        # -------------------------

        Notification.objects.get_or_create(
            title="Internal Examination Schedule",
            department="Computer Applications",
            semester="5",
            defaults={
                "description": (
                    "The internal examination schedule has been published. "
                    "Students are requested to check the examination timetable "
                    "and prepare accordingly."
                ),
                "is_important": True,
            },
        )

        Notification.objects.get_or_create(
            title="Assignment Submission Notice",
            department="Computer Applications",
            semester="",
            defaults={
                "description": (
                    "Students are reminded to submit their assignments "
                    "before the specified deadline."
                ),
                "is_important": True,
            },
        )

        Notification.objects.get_or_create(
            title="Department Meeting",
            department="Computer Applications",
            semester="",
            defaults={
                "description": (
                    "A department meeting has been scheduled. "
                    "Students are requested to check further details."
                ),
                "is_important": False,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "DNMS demo data created successfully."
            )
        )