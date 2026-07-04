import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        return 500, {"message": str(e)}

def test_login(username="admin", password="admin123"):
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    status, data = make_request(url, method="POST", data=payload)
    print(f"Login Status for {username}: {status}")
    if status == 200:
        print("Tokens received successfully")
        return data
    else:
        print(f"Error: {data}")
        return None

def test_me(access_token):
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    status, data = make_request(url, headers=headers)
    print(f"Me Response Status: {status}")
    print(f"Me Data: {data}")

def test_courses():
    url = f"{BASE_URL}/courses/"
    status, data = make_request(url)
    print(f"Courses Status: {status}")
    items = data.get('items', data)
    print(f"Total Courses: {len(items)}")

def test_enrollment(access_token):
    # Enroll
    url = f"{BASE_URL}/enrollments/?course_id=1"
    headers = {"Authorization": f"Bearer {access_token}"}
    status, data = make_request(url, method="POST", headers=headers)
    print(f"Enroll Status: {status} - {data.get('message', data)}")

    # My Courses
    url = f"{BASE_URL}/enrollments/my-courses"
    status, data = make_request(url, headers=headers)
    print(f"My Courses Status: {status}")
    print(f"Enrolled Count: {len(data)}")

def test_register():
    url = f"{BASE_URL}/auth/register"
    import random
    rand_user = f"user_{random.randint(1000, 9999)}"
    payload = {
        "username": rand_user,
        "email": f"{rand_user}@example.com",
        "password": "password123",
        "role": "student"
    }
    status, data = make_request(url, method="POST", data=payload)
    print(f"Register Status: {status}")
    if status == 201:
        print(f"User {rand_user} created successfully")
        return rand_user, "password123"
    else:
        print(f"Error: {data}")
        return None, None

if __name__ == "__main__":
    print("--- Testing API ---")
    
    # 1. Test Registration
    new_user, new_pass = test_register()
    
    # 2. Test Courses (Public)
    test_courses()
    
    # 3. Test Login with Admin
    print("\nAttempting Admin Login...")
    tokens = test_login("admin", "admin123")
    
    # 4. Test Login with New User if registration was successful
    if new_user:
        print(f"\nAttempting New User Login ({new_user})...")
        new_tokens = test_login(new_user, new_pass)
        if new_tokens:
            test_me(new_tokens['access'])
            test_enrollment(new_tokens['access'])
    
    if tokens:
        print("\nAdmin Profile Check:")
        test_me(tokens['access'])
