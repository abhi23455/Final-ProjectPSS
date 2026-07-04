#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import User
from courses.models import Category, Course

# Ensure instructor exists
instr, created = User.objects.get_or_create(
    username='instruktur_demo',
    defaults={'email': 'instruktur@demo.com'}
)
if created:
    instr.set_password('instruktur123')
    instr.role = 'instructor'
    instr.save()

# Ensure category
cat, _ = Category.objects.get_or_create(slug='demo-category', defaults={'name': 'Demo Category'})

# Create or update course with id=1
course_defaults = {
    'name': 'Demo Course',
    'slug': 'demo-course',
    'description': 'Course for testing',
    'category': cat,
    'instructor': instr,
    'price': 0.0,
}
course, created = Course.objects.update_or_create(id=1, defaults=course_defaults)
print(f"Course id=1 exists: {course.name} (created={created})")
