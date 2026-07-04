import os
import django
import time
from django.db import connection, reset_queries

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Q, Count, Avg, Max, Min, Sum
from courses.models import Course, Category, Lesson, Comment
from users.models import User

def setup_dummy_data():
    """Setup some dummy data if it doesn't exist"""
    # Clear existing demo data to avoid unique constraints if needed
    # Course.objects.filter(slug__startswith='course-').delete()
    
    instructor, _ = User.objects.get_or_create(
        username='demo_instructor', 
        defaults={'role': 'instructor'}
    )
    if not instructor.password:
        instructor.set_password('password')
        instructor.save()

    category, _ = Category.objects.get_or_create(
        slug='backend-development',
        defaults={'name': 'Backend Development'}
    )
    
    for i in range(10):
        course, created = Course.objects.get_or_create(
            slug=f'course-{i}',
            defaults={
                'name': f'Course {i}',
                'instructor': instructor,
                'category': category,
                'price': 10.0
            }
        )
        if created:
            for j in range(5):
                Lesson.objects.create(course=course, title=f'Lesson {j}', content='...', order=j)

def run_n_plus_one_demo():
    print("\n--- Running N+1 Problem Demo ---")
    reset_queries()
    start_time = time.time()
    
    # This triggers N+1 because it doesn't fetch instructor or category
    courses = Course.objects.all()
    
    print(f"Iterating through {len(courses)} courses and accessing related data:")
    for course in courses:
        # Each access here triggers a new SQL query if not optimized
        _ = course.instructor.username
        _ = course.category.name
        _ = course.lessons.count()
        
    end_time = time.time()
    query_count = len(connection.queries)
    print(f"Total Queries: {query_count}")
    print(f"Time taken: {end_time - start_time:.4f}s")

def run_optimized_demo():
    print("\n--- Running Optimized Query Demo ---")
    reset_queries()
    start_time = time.time()
    
    # Using for_listing() which uses select_related and annotate
    courses = Course.objects.for_listing()
    
    print(f"Iterating through {len(courses)} courses (Optimized):")
    for course in courses:
        # Related data is already fetched or annotated
        _ = course.instructor.username
        _ = course.category.name
        _ = course.enrollment_count
        
    end_time = time.time()
    query_count = len(connection.queries)
    print(f"Total Queries: {query_count}")
    print(f"Time taken: {end_time - start_time:.4f}s")

def run_relational_queries_demo():
    print("\n--- Running Relational Queries Demo ---")
    
    # 1. Forward Relation
    course = Course.objects.first()
    print(f"Course: {course.name}, Instructor: {course.instructor.username}")
    
    # 2. Reverse Relation (backward)
    category = Category.objects.get(slug='backend-development')
    print(f"Courses in {category.name}: {list(category.courses.values_list('name', flat=True))}")
    
    # 3. Filter with JOIN (double underscore)
    django_courses = Course.objects.filter(category__name__icontains='backend')
    print(f"Backend courses: {django_courses.count()}")
    
    # 4. Aggregate
    stats = Course.objects.aggregate(
        total=Count('id'),
        avg_price=Avg('price'),
        max_price=Max('price')
    )
    print(f"Stats: {stats}")
    
    # 5. Q Objects (OR condition)
    or_query = Course.objects.filter(
        Q(price__lt=60000) | Q(name__icontains='React')
    )
    print(f"Courses (price < 60k OR name contains 'React'): {or_query.count()}")

def cleanup_dummy_data():
    """Hapus data dummy setelah demo selesai."""
    Course.objects.filter(slug__startswith='course-').delete()
    print("\n✅ Data dummy course-0 s/d course-9 sudah dibersihkan.")

if __name__ == "__main__":
    setup_dummy_data()
    run_n_plus_one_demo()
    run_optimized_demo()
    run_relational_queries_demo()
    cleanup_dummy_data()
