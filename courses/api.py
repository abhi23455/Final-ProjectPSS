# courses/api.py
# Integrasi Redis Cache sesuai buku Chapter 10 Section 7
# Pattern: Cache-Aside untuk read, Write-Through (invalidation) untuk write

from ninja import Router
from ninja.pagination import paginate
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.core.cache import cache              # Django Cache Framework
from django_redis import get_redis_connection    # Untuk operasi Redis langsung
from typing import List, Optional
import json

from .models import Course, Category, Enrollment, Progress, Lesson, Certificate
from .schemas import (
    CourseOut, CourseDetailOut, CourseCreateSchema, CourseUpdateSchema,
    EnrollmentOut, ProgressSchema, CategorySchema, CertificateOut
)
from config.permissions import role_required, is_instructor, is_admin
from ninja.errors import HttpError
from django.db.models import Count, Q
from config.utils import rate_limit
from .mongo_models import ActivityLog, LearningAnalytics
from .tasks import send_enrollment_email, generate_certificate, export_course_report
from celery.result import AsyncResult

router = Router(tags=["Courses"])
enrollment_router = Router(tags=["Enrollments"])
analytics_router = Router(tags=["Analytics"])


# ==============================
# HELPER: map_course
# ==============================
def map_course(c):
    return {
        "id": c.id,
        "name": c.name,
        "slug": c.slug,
        "description": c.description,
        "category": {
            "id": c.category.id,
            "name": c.category.name,
            "slug": c.category.slug
        },
        "instructor_username": c.instructor.username,
        "price": float(c.price),
        "enrollment_count": getattr(c, 'enrollment_count', 0)
    }


# ==============================
# HELPER: Cache Invalidation
# Sesuai buku Chapter 10 Section 7.2 (Write-Through)
# ==============================
def invalidate_course_caches(course_id=None):
    """
    Hapus semua cache terkait course.
    Dipanggil setiap kali ada create, update, atau delete course.
    """
    # Hapus cache list courses
    cache.delete('courses_list')

    # Hapus cache detail course jika id diberikan
    if course_id:
        cache.delete(f'course_detail:{course_id}')


# ============================================================
# COURSES PUBLIC ENDPOINTS
# ============================================================

@router.get("/", response=List[CourseOut])
@rate_limit(limit=60, period=60)
@paginate
def list_courses(
    request,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    ordering: str = "-created_at"
):
    """
    Mengambil daftar semua course dengan filter dan pagination.

    Menggunakan Cache-Aside pattern:
    - Cek cache dulu dengan key 'courses_list'
    - Jika cache hit: return dari Redis (cepat)
    - Jika cache miss: query PostgreSQL, simpan ke Redis, return data
    Sesuai buku Chapter 10 Section 7.1
    """
    # Buat cache key unik berdasarkan semua parameter filter
    cache_key = f'courses_list:{category_id}:{search}:{min_price}:{max_price}:{ordering}'

    # 1. Cek cache — Cache-Aside pattern
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # 2. Cache miss — query database
    qs = Course.objects.for_listing()
    if category_id:
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    courses = [map_course(c) for c in qs.order_by(ordering)]

    # 3. Simpan ke cache dengan TTL 5 menit
    cache.set(cache_key, courses, timeout=300)

    return courses


@router.get("/popular/", response=List[dict])
def popular_courses(request):
    """
    Menampilkan top 10 course terpopuler berdasarkan jumlah enrollment.
    Menggunakan Redis Sorted Set (ZREVRANGE).
    Sesuai buku Chapter 10 Section 4.4 dan Latihan 3.
    """
    redis_conn = get_redis_connection("default")

    # Ambil top 10 dari sorted set
    top = redis_conn.zrevrange('simple_lms:popular_courses', 0, 9, withscores=True)

    if not top:
        # Jika sorted set kosong, isi dari database
        courses = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]

        for c in courses:
            redis_conn.zadd(
                'simple_lms:popular_courses',
                {str(c.id): c.enrollment_count}
            )

        top = redis_conn.zrevrange('simple_lms:popular_courses', 0, 9, withscores=True)

    result = []
    for course_id_bytes, score in top:
        course_id = int(course_id_bytes)
        try:
            c = Course.objects.select_related('instructor', 'category').get(pk=course_id)
            result.append({
                "id": c.id,
                "name": c.name,
                "instructor_username": c.instructor.username,
                "enrollment_count": int(score)
            })
        except Course.DoesNotExist:
            pass

    return result


@router.get("/{id}", response=CourseDetailOut)
@rate_limit(limit=60, period=60)
def get_course(request, id: int):
    """
    Detail course beserta daftar materi.

    Menggunakan Cache-Aside pattern dengan key 'course_detail:{id}'.
    Sesuai buku Chapter 10 Latihan 1.
    """
    cache_key = f'course_detail:{id}'

    # 1. Cek cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # 2. Cache miss — query database
    course = get_object_or_404(Course.objects.for_listing(), id=id)
    lessons = course.lessons.all()

    data = map_course(course)
    data["lessons"] = [
        {
            "id": l.id,
            "title": l.title,
            "order": l.order,
            "video_url": l.video_url,
            "content": l.content
        } for l in lessons
    ]

    # 3. Simpan ke cache dengan TTL 5 menit
    cache.set(cache_key, data, timeout=300)

    return data


# ============================================================
# COURSES PROTECTED ENDPOINTS
# ============================================================

@router.post("/", auth=JWTAuth(), response={201: CourseOut, 403: dict})
@is_instructor
def create_course(request, data: CourseCreateSchema):
    """
    Membuat course baru (Hanya Instructor).
    Invalidasi cache list setelah create.
    Sesuai buku Chapter 10 Section 7.2 (Write-Through).
    """
    category = get_object_or_404(Category, id=data.category_id)
    course = Course.objects.create(
        name=data.name,
        slug=data.slug,
        description=data.description,
        category=category,
        instructor=request.auth,
        price=data.price
    )
    course = Course.objects.for_listing().get(id=course.id)

    # Invalidasi cache list karena ada data baru
    invalidate_course_caches()

    return 201, map_course(course)


@router.patch("/{id}", auth=JWTAuth(), response={200: CourseOut, 403: dict})
@is_instructor
def update_course(request, id: int, data: CourseUpdateSchema):
    """
    Update data course (Hanya Owner/Admin).
    Invalidasi cache list DAN cache detail setelah update.
    Sesuai buku Chapter 10 Section 7.2 Latihan 2.
    """
    course = get_object_or_404(Course, id=id)
    if course.instructor != request.auth and request.auth.role != 'admin':
        raise HttpError(403, "You are not the owner of this course")

    for attr, value in data.dict(exclude_unset=True).items():
        setattr(course, attr, value)
    course.save()

    course = Course.objects.for_listing().get(id=course.id)

    # Invalidasi cache list dan detail — sesuai buku Latihan 2
    invalidate_course_caches(course_id=id)

    return map_course(course)


@router.delete("/{id}", auth=JWTAuth(), response={204: None, 403: dict})
@is_admin
def delete_course(request, id: int):
    """
    Hapus course (Hanya Admin).
    Invalidasi semua cache terkait course.
    Sesuai buku Chapter 10 Section 7.2 Latihan 2.
    """
    course = get_object_or_404(Course, id=id)
    course.delete()

    # Invalidasi cache list dan detail — sesuai buku Latihan 2
    invalidate_course_caches(course_id=id)

    return 204, None


# ============================================================
# ENROLLMENT ENDPOINTS
# ============================================================

@enrollment_router.post("/", auth=JWTAuth(), response={201: dict, 400: dict})
def enroll_course(request, course_id: int):
    """
    Mendaftar ke course (Student).
    Update leaderboard Redis Sorted Set saat ada enrollment baru.
    Trigger Celery task untuk kirim email konfirmasi (async),
    dan kembalikan task_id-nya supaya bisa dicek statusnya.
    Sesuai buku Chapter 10 Latihan 3 + Final Project Paket 6 (Async Processing).
    """
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.auth,
        course=course
    )
    if not created:
        return 400, {"message": "Already enrolled"}

    # Update score di leaderboard sorted set
    # Sesuai buku Chapter 10 Section 5.5 — ZINCRBY
    redis_conn = get_redis_connection("default")
    redis_conn.zincrby('simple_lms:popular_courses', 1, str(course_id))

    # Log activity to MongoDB
    ActivityLog(
        user_id=request.auth.id,
        username=request.auth.username,
        action="COURSE_ENROLL",
        details={"course_id": course.id, "course_name": course.name},
        ip_address=request.META.get('REMOTE_ADDR')
    ).save()

    # Trigger Celery task for email — tangkap AsyncResult-nya
    task = send_enrollment_email.delay(
        request.auth.email,
        request.auth.username,
        course.name
    )

    return 201, {
        "message": "Enrolled successfully! Check your email for confirmation.",
        "enrollment": {
            "id": enrollment.id,
            "course_id": map_course(course),
            "roles": request.auth.role
        },
        "task_id": task.id
    }


@enrollment_router.get("/tasks/{task_id}/status", auth=JWTAuth())
def get_task_status(request, task_id: str):
    """
    Cek status Celery task berdasarkan task_id yang didapat
    dari response endpoint enroll_course (atau task async lainnya).
    Status yang mungkin: PENDING, STARTED, SUCCESS, FAILURE.
    Membutuhkan CELERY_RESULT_BACKEND (sudah diset ke 'django-db' di settings).
    """
    result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }


@enrollment_router.get("/my-courses", auth=JWTAuth(), response=List[dict])
def my_courses(request):
    """
    Daftar course yang diikuti oleh user saat ini.
    Termasuk detail course dan daftar materi (Lesson)!
    """
    qs = Enrollment.objects.for_student_dashboard().filter(user=request.auth)
    result = []
    for e in qs:
        # Ambil daftar lesson beserta status selesai
        lessons = e.course.lessons.all()
        lesson_list = []
        for l in lessons:
            # Cek apakah lesson ini sudah diselesaikan oleh user
            is_completed = Progress.objects.filter(
                user=request.auth, 
                lesson=l
            ).exists()
            lesson_list.append({
                "id": l.id,
                "title": l.title,
                "order": l.order,
                "is_completed": is_completed
            })
        
        result.append({
            "id": e.id,
            "course": {
                "id": e.course.id,
                "name": e.course.name,
                "description": e.course.description,
                "instructor_username": e.course.instructor.username
            },
            "enrolled_at": e.enrolled_at,
            "progress_percent": (
                e.completed_lessons_count / e.total_lessons_count * 100
            ) if e.total_lessons_count > 0 else 0,
            "lessons": lesson_list
        })
    return result


@enrollment_router.post("/{enrollment_id}/progress", auth=JWTAuth(), response={200: dict, 403: dict})
def mark_progress(request, enrollment_id: int, data: ProgressSchema):
    """
    Menandai materi sebagai selesai berdasarkan pendaftaran.
    """
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.auth)
    lesson = get_object_or_404(Lesson, id=data.lesson_id, course=enrollment.course)

    Progress.objects.update_or_create(
        user=request.auth,
        lesson=lesson,
        defaults={"is_completed": data.is_completed}
    )

    # Log to MongoDB
    LearningAnalytics(
        course_id=enrollment.course.id,
        student_id=request.auth.id,
        activity_type='lesson_progress',
        details={"lesson_id": lesson.id, "is_completed": data.is_completed}
    ).save()

    # Check if course is completed
    total_lessons = Lesson.objects.filter(course=enrollment.course).count()
    completed_lessons = Progress.objects.filter(
        user=request.auth, 
        lesson__course=enrollment.course,
        is_completed=True
    ).count()

    if total_lessons > 0 and total_lessons == completed_lessons:
        # Trigger certificate generation
        generate_certificate.delay(request.auth.id, enrollment.course.id)
        
        # Log completion
        ActivityLog(
            user_id=request.auth.id,
            username=request.auth.username,
            action="COURSE_COMPLETE",
            details={"course_id": enrollment.course.id, "course_name": enrollment.course.name}
        ).save()

    return {"message": "Progress updated"}


# ============================================================
# SESSION ENDPOINTS — Sesuai buku Chapter 10 Latihan 4
# ============================================================

@router.post("/{id}/visit/")
def visit_course(request, id: int):
    """
    Mencatat kunjungan user ke halaman course menggunakan session Redis.
    Sesuai buku Chapter 10 Section 8.3.
    """
    get_object_or_404(Course, id=id)

    visited = request.session.get('visited_courses', [])
    if id not in visited:
        visited.append(id)
        request.session['visited_courses'] = visited

    return {
        "course_id": id,
        "total_visited": len(visited),
        "visited_courses": visited
    }

# ============================================================
# ANALYTICS & REPORTS ENDPOINTS
# ============================================================

@analytics_router.get("/reports/course/{course_id}")
@is_instructor
def trigger_course_report(request, course_id: int):
    """
    Trigger async CSV report generation.
    """
    export_course_report.delay(course_id)
    return {"message": "Report generation started. You will be notified when it is ready."}

@analytics_router.get("/stats/course/{course_id}")
@is_instructor
def get_course_stats(request, course_id: int):
    """
    Get aggregated analytics for a course from MongoDB.
    """
    pipeline = [
        {"$match": {"course_id": course_id}},
        {"$group": {
            "_id": "$activity_type",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$score"}
        }}
    ]
    results = LearningAnalytics.objects.aggregate(*pipeline)
    return list(results)

@analytics_router.get("/logs/user/{user_id}")
@is_admin
def get_user_logs(request, user_id: int):
    """
    Get activity logs for a specific user from MongoDB.
    """
    logs = ActivityLog.objects(user_id=user_id).order_by('-timestamp').limit(50)
    return [json.loads(log.to_json()) for log in logs]

# ============================================================
# CERTIFICATES ENDPOINTS
# ============================================================
certificates_router = Router(tags=["Certificates"])

@certificates_router.get("/my-certificates", auth=JWTAuth(), response=List[CertificateOut])
def my_certificates(request):
    """
    Lihat semua sertifikat milik user saat ini.
    """
    certs = Certificate.objects.filter(user=request.auth).select_related('course')
    return [
        {
            "id": c.id,
            "certificate_code": c.certificate_code,
            "course_name": c.course.name,
            "issued_at": c.issued_at,
            "pdf_url": request.build_absolute_uri(c.pdf_file.url) if c.pdf_file else None
        } for c in certs
    ]

@certificates_router.post("/generate/{course_id}", auth=JWTAuth(), response={200: dict, 400: dict})
def generate_certificate_endpoint(request, course_id: int):
    """
    Generate sertifikat secara manual untuk course tertentu.
    OTOMATIS menandai SEMUA lesson sebagai selesai!
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Cek enrollment
    enrollment = get_object_or_404(Enrollment, user=request.auth, course=course)
    
    # 🔥 OTOMATIS TANDAI SEMUA LESSON SELESAI!
    from .models import Lesson, Progress
    lessons = Lesson.objects.filter(course=course)
    for lesson in lessons:
        Progress.objects.update_or_create(
            user=request.auth,
            lesson=lesson,
            defaults={'is_completed': True}
        )
    
    # Trigger async task
    generate_certificate.delay(request.auth.id, course.id)
    return {"message": "Certificate generation started! All lessons marked as completed!"}

from django.http import FileResponse
@certificates_router.get("/download/{cert_id}", auth=JWTAuth())
def download_certificate(request, cert_id: int):
    """
    DOWNLOAD PDF sertifikat secara langsung!
    """
    cert = get_object_or_404(Certificate, id=cert_id, user=request.auth)
    if not cert.pdf_file:
        raise HttpError(404, "Certificate PDF not found")
    response = FileResponse(cert.pdf_file.open(), as_attachment=True, filename=f"certificate_{cert.certificate_code}.pdf")
    return response