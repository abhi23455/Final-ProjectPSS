#!/usr/bin/env python
"""Script untuk mengisi data awal course dan lesson ke database."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import User
from courses.models import Category, Course, Lesson

print("="*60)
print("MENGISI DATA AWAL SIMPLE LMS")
print("="*60)

# 1. Buat Kategori
print("\nMembuat kategori...")
cat_prog, created = Category.objects.get_or_create(
    name="Pemrograman Web",
    defaults={"slug": "pemrograman-web"}
)
print(f"✅ Kategori '{cat_prog.name}' siap!")

# 2. Dapatkan Instructor Demo
print("\nMencari instruktur...")
try:
    instructor = User.objects.get(username="instruktur_demo")
    print(f"✅ Instruktur '{instructor.username}' ditemukan!")
except User.DoesNotExist:
    print("⚠️  Instruktur tidak ditemukan, membuat baru...")
    instructor = User.objects.create_user(
        username="instruktur_demo",
        email="instruktur@demo.com",
        password="instruktur123",
        role="instructor"
    )
    print(f"✅ Instruktur '{instructor.username}' dibuat!")

# 3. Buat Course & Lesson
print("\nMembuat course dan materi...")

# Course 1: HTML & CSS Dasar
course1, created = Course.objects.get_or_create(
    name="HTML & CSS Dasar",
    defaults={
        "slug": "html-css-dasar",
        "description": "Belajar membuat website dari nol dengan HTML dan CSS.",
        "category": cat_prog,
        "instructor": instructor,
        "price": 0
    }
)
if created:
    print(f"✅ Course '{course1.name}' dibuat!")
    
    # Buat lesson untuk course 1
    lessons1 = [
        {"title": "Pengenalan HTML", "content": "Pelajari dasar-dasar tag HTML.", "order": 1},
        {"title": "Struktur Website", "content": "Struktur dasar sebuah website dengan HTML5.", "order": 2},
        {"title": "Styling dengan CSS", "content": "Belajar CSS untuk mempercantik tampilan website.", "order": 3}
    ]
    for lesson_data in lessons1:
        Lesson.objects.create(course=course1, **lesson_data)
    print(f"✅ {len(lessons1)} materi untuk course 1 dibuat!")

# Course 2: Javascript Dasar
course2, created = Course.objects.get_or_create(
    name="Javascript Dasar",
    defaults={
        "slug": "javascript-dasar",
        "description": "Belajar dasar-dasar pemrograman Javascript.",
        "category": cat_prog,
        "instructor": instructor,
        "price": 0
    }
)
if created:
    print(f"✅ Course '{course2.name}' dibuat!")
    
    lessons2 = [
        {"title": "Variabel & Tipe Data", "content": "Belajar variabel dan tipe data di JS.", "order": 1},
        {"title": "Pengkondisian", "content": "If else dan switch di Javascript.", "order": 2}
    ]
    for lesson_data in lessons2:
        Lesson.objects.create(course=course2, **lesson_data)
    print(f"✅ {len(lessons2)} materi untuk course 2 dibuat!")

print("\n" + "="*60)
print("SELESAI! DATA AWAL SUDAH TERISI!")
print("="*60)
print(f"Total kursus: {Course.objects.count()}")
print(f"Total materi: {Lesson.objects.count()}")
