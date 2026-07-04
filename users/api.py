from ninja import Router
from django.contrib.auth import authenticate
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.authentication import JWTAuth
from .models import User
from .schemas import RegisterSchema, UserOut, ProfileUpdateSchema, LoginSchema

router = Router(tags=["Auth"])


@router.post("/register", auth=None, response={201: UserOut, 400: dict})
def register(request, data: RegisterSchema):
    if User.objects.filter(username=data.username).exists():
        return 400, {"message": "Username already exists"}
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        role=data.role
    )
    return 201, user


@router.post("/login", auth=None)
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    # Generate real JWT using ninja_jwt
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }


@router.get("/me", auth=JWTAuth(), response=UserOut)
def me(request):
    user = request.auth if hasattr(request, 'auth') and request.auth else None
    if not user:
        raise HttpError(401, "Authentication required")
    return user