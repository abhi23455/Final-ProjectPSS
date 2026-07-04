from ninja import NinjaAPI
from ninja.security import HttpBearer
from ninja_jwt.authentication import JWTAuth
from users.api import router as auth_router
from courses.api import router as courses_router, enrollment_router, analytics_router, certificates_router

# Custom security class to make Swagger recognize Bearer Auth correctly
class GlobalJWTAuth(JWTAuth):
    def __call__(self, request):
        return super().__call__(request)

api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="REST API for Learning Management System",
    auth=None  # Keep docs/openapi public; protect routers individually
)

# Auth endpoints (Register, Login, Refresh, Me, Update Profile)
# We override auth=None for login and register so they are public
api.add_router("/auth", auth_router, auth=None)

# Course endpoints
api.add_router("/courses", courses_router, auth=None) # List and Detail are public

# Enrollment endpoints
api.add_router("/enrollments", enrollment_router, auth=JWTAuth())

# Analytics & Reports endpoints
api.add_router("/analytics", analytics_router, auth=JWTAuth())

# Certificates endpoints
api.add_router("/certificates", certificates_router, auth=JWTAuth())
