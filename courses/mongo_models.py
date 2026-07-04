from mongoengine import Document, StringField, DateTimeField, IntField, DictField, ReferenceField
from datetime import datetime

class ActivityLog(Document):
    user_id = IntField(required=True)
    username = StringField(max_length=150)
    action = StringField(required=True)
    details = DictField()
    timestamp = DateTimeField(default=datetime.utcnow)
    ip_address = StringField()

    meta = {
        'collection': 'activity_logs',
        'indexes': ['user_id', 'action', 'timestamp']
    }

class LearningAnalytics(Document):
    course_id = IntField(required=True)
    student_id = IntField(required=True)
    activity_type = StringField()  # e.g., 'video_watch', 'quiz_attempt', 'module_complete'
    details = DictField()
    duration = IntField()  # in seconds
    score = IntField(null=True)
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'learning_analytics',
        'indexes': ['course_id', 'student_id', 'timestamp']
    }
