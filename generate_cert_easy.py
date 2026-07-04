#!/usr/bin/env python
"""Script MUDAH untuk tandai semua lesson selesai dan generate certificate!"""
import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import User
from courses.models import Course, Lesson, Progress, Enrollment
from courses.tasks import generate_certificate

# Dapatkan username dari argument, default: siswa_demo
username = sys.argv[1] if len(sys.argv) > 1 else 'siswa_demo'
course_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

print("="*60)
print(f"MEMBUAT CERTIFICATE UNTUK USER: {username}")
print("="*60)

# 1. Dapatkan user, course, dan enrollment
user = User.objects.get(username=username)
course = Course.objects.get(id=course_id)
enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
print(f"User: {user.username}")
print(f"Course: {course.name}")

# 2. TANDAI SEMUA LESSON SELESAI!
lessons = Lesson.objects.filter(course=course)
print(f"\nMenandai {len(lessons)} lesson selesai...")
for lesson in lessons:
    Progress.objects.update_or_create(
        user=user,
        lesson=lesson,
        defaults={'is_completed': True}
    )
print("✅ Semua lesson ditandai selesai!")

# 3. GENERATE CERTIFICATE!
print("\nMembuat certificate...")
result = generate_certificate(user.id, course.id)
print(f"✅ Hasil: {result}")

print("\n" + "="*60)
print("SELESAI! SILAKAN CEK DI SWAGGER UI!")
print("="*60)
