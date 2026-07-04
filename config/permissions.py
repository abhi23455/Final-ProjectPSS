from ninja.errors import HttpError
from functools import wraps

def role_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # request.auth is populated by Ninja when using JWTAuth()
            user = request.auth
            if not user or user.role not in roles:
                raise HttpError(403, "Permission Denied: Unauthorized role")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# Convenience decorators
def is_instructor(func):
    return role_required(['instructor', 'admin'])(func)

def is_admin(func):
    return role_required(['admin'])(func)

def is_student(func):
    return role_required(['student', 'admin'])(func)
