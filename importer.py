import csv
import django
import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment, Category

User = get_user_model()

def import_courses(csv_file):
    """Import data course dari file CSV."""
    if not os.path.exists(csv_file):
        print(f"[ERROR] File {csv_file} tidak ditemukan")
        return

    print(f"=== Importing Courses from {csv_file} ===")
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                instructor = User.objects.get(username=row['instructor_username'])
                category = Category.objects.get(slug=row['category_slug'])
                
                course, created = Course.objects.update_or_create(
                    slug=row['slug'],
                    defaults={
                        'name': row['name'],
                        'description': row['description'],
                        'price': float(row['price']),
                        'instructor': instructor,
                        'category': category,
                    }
                )
                if created:
                    print(f"[CREATED] Course: {course.name}")
                else:
                    print(f"[UPDATED] Course: {course.name}")
            except User.DoesNotExist:
                print(f"[SKIP] Instructor {row['instructor_username']} tidak ditemukan")
            except Category.DoesNotExist:
                print(f"[SKIP] Category {row['category_slug']} tidak ditemukan")
            except Exception as e:
                print(f"[ERROR] {str(e)}")

def import_enrollments(csv_file):
    """Import data pendaftaran dari file CSV."""
    if not os.path.exists(csv_file):
        print(f"[ERROR] File {csv_file} tidak ditemukan")
        return

    print(f"\n=== Importing Enrollments from {csv_file} ===")
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                course = Course.objects.get(slug=row['course_slug'])
                user = User.objects.get(username=row['username'])
                
                enrollment, created = Enrollment.objects.get_or_create(
                    course=course,
                    user=user
                )
                if created:
                    print(f"[CREATED] Enrollment: {user.username} -> {course.name}")
                else:
                    print(f"[EXISTS]  Enrollment: {user.username} -> {course.name}")
            except Course.DoesNotExist:
                print(f"[SKIP] Course {row['course_slug']} tidak ditemukan")
            except User.DoesNotExist:
                print(f"[SKIP] User {row['username']} tidak ditemukan")
            except Exception as e:
                print(f"[ERROR] {str(e)}")

if __name__ == '__main__':
    import_courses('courses/fixtures/courses.csv')
    import_enrollments('courses/fixtures/members.csv')
    print("\nImport selesai!")
