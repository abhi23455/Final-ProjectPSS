import csv
import os
import uuid
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, Enrollment, Certificate
from .mongo_models import ActivityLog, LearningAnalytics
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.core.files.base import ContentFile

@shared_task
def send_enrollment_email(student_email, student_name, course_name):
    subject = f'Welcome to {course_name}'
    message = f'Hi {student_name},\n\nYou have successfully enrolled in {course_name}. Happy learning!'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [student_email]
    send_mail(subject, message, email_from, recipient_list)
    
    # Log to MongoDB
    ActivityLog(
        user_id=0, # System or use actual user_id if passed
        username="System",
        action="EMAIL_SENT",
        details={"type": "enrollment", "email": student_email, "course": course_name}
    ).save()

    # Return value supaya muncul di kolom "Result" Flower dan
    # bisa dibaca lewat endpoint /tasks/{task_id}/status
    return f"Email sent to {student_email} for course {course_name}"

@shared_task
def generate_certificate(student_id, course_id):
    try:
        from users.models import User
        from .models import Lesson
        student = User.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)
        lessons = Lesson.objects.filter(course=course).order_by('order')
        
        # Check if certificate already exists
        cert, created = Certificate.objects.get_or_create(
            user=student,
            course=course,
            defaults={'certificate_code': f"CERT-{uuid.uuid4().hex[:8].upper()}"}
        )
        
        if not created:
            return f"Certificate already exists for {student.username} in {course.name}"
        
        # Generate PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Title
        p.setFont("Helvetica-Bold", 24)
        p.setFillColor(colors.darkblue)
        p.drawCentredString(width / 2, height - 100, "CERTIFICATE OF COMPLETION")
        
        # Decorative line
        p.setStrokeColor(colors.goldenrod)
        p.setLineWidth(3)
        p.line(100, height - 120, width - 100, height - 120)
        
        # Content
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 180, "This is to certify that")
        
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(colors.darkred)
        p.drawCentredString(width / 2, height - 230, student.username.upper())
        
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 280, "has successfully completed the course")
        
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.darkgreen)
        p.drawCentredString(width / 2, height - 330, course.name.upper())
        
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 400, f"Certificate Code: {cert.certificate_code}")
        p.drawCentredString(width / 2, height - 430, f"Issued on: {datetime.now().strftime('%Y-%m-%d')}")
        
        # TAMBAH DAFTAR LESSON!
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.darkblue)
        y = height - 480
        p.drawString(100, y, "Lessons Completed:")
        
        p.setFont("Helvetica", 10)
        p.setFillColor(colors.black)
        y -= 25
        for i, lesson in enumerate(lessons):
            p.drawString(120, y, f"{i+1}. {lesson.title}")
            y -= 15
            if y < 200:
                break
        
        # Signature
        p.setFont("Helvetica-Oblique", 12)
        p.drawString(100, 150, "Instructor: _____________________")
        p.drawString(width - 200, 150, "Admin: _____________________")
        
        p.showPage()
        p.save()
        
        # Save PDF to model
        buffer.seek(0)
        pdf_content = buffer.getvalue()
        pdf_filename = f"certificate_{student.username}_{course.id}.pdf"
        cert.pdf_file.save(pdf_filename, ContentFile(pdf_content), save=True)
        
        # Log to MongoDB
        ActivityLog(
            user_id=student_id,
            username=student.username,
            action="CERTIFICATE_GENERATED",
            details={"course_id": course_id, "course_title": course.name, "certificate_code": cert.certificate_code}
        ).save()
        
        return f"Certificate generated for {student.username} in {course.name}"
    except Exception as e:
        return str(e)

@shared_task
def update_course_statistics():
    courses = Course.objects.all()
    for course in courses:
        enrollment_count = Enrollment.objects.filter(course=course).count()
        # Assume there's an enrollment_count field or similar we want to sync/log
        # For this exercise, let's log the stats to MongoDB
        LearningAnalytics(
            course_id=course.id,
            student_id=0, # System
            activity_type='stats_update',
            duration=0,
            score=enrollment_count,
            timestamp=datetime.utcnow()
        ).save()
    return f"Updated statistics for {courses.count()} courses"

@shared_task
def export_course_report(course_id):
    try:
        course = Course.objects.get(id=course_id)
        enrollments = Enrollment.objects.filter(course=course)
        
        filename = f'course_{course_id}_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Student Username', 'Enrollment Date', 'Status'])
            for enrollment in enrollments:
                writer.writerow([enrollment.user.username, enrollment.enrolled_at, 'Enrolled'])
        
        ActivityLog(
            user_id=0,
            username="System",
            action="REPORT_EXPORTED",
            details={"course_id": course_id, "file": filename}
        ).save()
        
        return f"Report generated: {filename}"
    except Exception as e:
        return str(e)