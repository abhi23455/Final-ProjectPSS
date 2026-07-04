#!/usr/bin/env python
"""Script untuk membuat akun demo secara otomatis."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import User

# Daftar akun demo
AKUN_DEMO = [
    {
        "username": "admin_demo",
        "email": "admin@demo.com",
        "password": "admin123",
        "role": "admin",
        "is_superuser": True,
    },
    {
        "username": "instruktur_demo",
        "email": "instruktur@demo.com",
        "password": "instruktur123",
        "role": "instructor",
        "is_superuser": False,
    },
    {
        "username": "siswa_demo",
        "email": "siswa@demo.com",
        "password": "siswa123",
        "role": "student",
        "is_superuser": False,
    },
]

print("="*50)
print("Membuat Akun Demo Simple LMS")
print("="*50)

for akun in AKUN_DEMO:
    # Hapus jika sudah ada
    User.objects.filter(username=akun["username"]).delete()
    
    # Buat baru
    if akun["is_superuser"]:
        user = User.objects.create_superuser(
            username=akun["username"],
            email=akun["email"],
            password=akun["password"],
        )
    else:
        user = User.objects.create_user(
            username=akun["username"],
            email=akun["email"],
            password=akun["password"],
        )
    
    user.role = akun["role"]
    user.save()
    
    print(f"✅ {akun['username']} ({akun['role']}) berhasil dibuat!")

print("\n" + "="*50)
print("Akun Demo Selesai!")
print("="*50)
print("Admin:    admin_demo / admin123")
print("Instruktur: instruktur_demo / instruktur123")
print("Siswa:    siswa_demo / siswa123")
print("\nJalankan project dengan: docker-compose up -d")
