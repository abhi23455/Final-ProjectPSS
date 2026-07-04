from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str

class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    category: CategorySchema
    instructor_username: str
    price: float
    enrollment_count: int

class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    order: int
    video_url: Optional[str] = None
    content: Optional[str] = None

class CourseDetailOut(CourseOut):
    lessons: List[LessonOut]

class CourseCreateSchema(BaseModel):
    name: str
    slug: str
    description: str
    category_id: int
    price: float = 0.0

class CourseUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class EnrollmentOut(BaseModel):
    id: int
    course_name: str
    enrolled_at: datetime
    progress_percent: float = 0.0

class ProgressSchema(BaseModel):
    lesson_id: int
    is_completed: bool = True

class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    certificate_code: str
    course_name: str
    issued_at: datetime
    pdf_url: Optional[str] = None
