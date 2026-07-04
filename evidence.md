Evidence for Paket 4 (Performance & API Quality)

Commands executed (run inside project root):

1. Start services

```bash
docker compose up -d --build
```

2. Apply migrations

```bash
docker compose exec web python manage.py migrate --noinput
```

3. Create demo course (id=1)

```bash
docker compose exec web python create_demo_course.py
```

4. Run API tests

```bash
# executed on host
docker compose exec web python test_api.py
```

Captured test output (summary):

- Register: 201 Created
- Courses: 200 OK (6 items)
- Login (admin & new user): 200 OK, tokens received
- /auth/me: 200 OK (returns user profile)
- Enroll: 201 Created
- My Courses: 200 OK (enrolled count 1)

Full latest test run output (copied):

--- Testing API ---
Register Status: 201
User user_6628 created successfully
Courses Status: 200
Total Courses: 6

Attempting Admin Login...
Login Status for admin: 200
Tokens received successfully

Attempting New User Login (user_6628)...
Login Status for user_6628: 200
Tokens received successfully
Me Response Status: 200
Me Data: {'id': 26, 'username': 'user_6628', 'email': 'user_6628@example.com', 'role': 'student', 'bio': None}
Enroll Status: 201 - Enrolled successfully! Check your email for confirmation.
My Courses Status: 200
Enrolled Count: 1

Admin Profile Check:
Me Response Status: 200
Me Data: {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'role': 'admin', 'bio': None}

Screenshots saved in workspace (relative paths):
- Swagger UI: .vscode/call_Ry4IciMGIvfPo4WVOO6YQFA9/0/file.jpe (attached in chat)
- Django Admin login: .vscode/call_EUH7vn6G1QsE3osltFTKPp2n/0/file.jpe (attached in chat)
- Flower dashboard: .vscode/call_typp59eY7evAnr20x7jnzQMm/0/file.jpe (attached in chat)

Notes:
- Swagger is available at http://localhost:8000/api/docs
- Django admin at http://localhost:8000/admin/ (use demo admin credentials)
- Flower at http://localhost:5555/


Prepared by the automated check script.
