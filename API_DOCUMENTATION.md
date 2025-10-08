# Authentication API Documentation

This document describes the secure authentication API endpoints for the nodews project, designed to be ready for deployment as auth.szlg.info.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://auth.szlg.info` (future)

## API Endpoints

### 1. User Registration
**POST** `/api/register/`

Register a new user account.

**Request Body:**
```json
{
    "username": "string",
    "email": "string",
    "password1": "string",
    "password2": "string",
    "first_name": "string (optional)",
    "last_name": "string (optional)"
}
```

**Success Response (201):**
```json
{
    "success": true,
    "message": "User created successfully",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

**Error Response (400):**
```json
{
    "error": {
        "username": ["This field is required."],
        "password1": ["This password is too short."]
    }
}
```

### 2. User Login
**POST** `/api/login/`

Authenticate a user and create a session.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_staff": false,
        "is_active": true,
        "date_joined": "2025-10-08T13:46:14.123456Z"
    }
}
```

**Error Response (401):**
```json
{
    "error": "Invalid credentials"
}
```

### 3. User Logout
**POST** `/api/logout/`

Logout the current user and destroy the session.

**Headers:**
- Requires active session or authentication

**Success Response (200):**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

**Error Response (401):**
```json
{
    "error": "Not authenticated"
}
```

### 4. Get User Information
**GET** `/api/user/`

Get information about the currently authenticated user.

**Headers:**
- Requires active session or authentication

**Success Response (200):**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_staff": false,
        "is_active": true,
        "date_joined": "2025-10-08T13:46:14.123456Z",
        "last_login": "2025-10-08T14:30:22.654321Z"
    }
}
```

**Error Response (401):**
```json
{
    "error": "Not authenticated"
}
```

## Security Features

### Production Security (for auth.szlg.info)

The application includes comprehensive security configurations:

1. **HTTPS Enforcement**
   - SSL redirect
   - HSTS headers
   - Secure proxy headers

2. **Session Security**
   - Secure cookies
   - HttpOnly cookies
   - SameSite strict
   - 24-hour session timeout

3. **CSRF Protection**
   - Secure CSRF tokens
   - HttpOnly CSRF cookies
   - SameSite strict

4. **CORS Configuration**
   - Configurable allowed origins
   - Secure cross-origin requests

5. **Rate Limiting** (ready for implementation)
   - API endpoint protection
   - Brute force prevention

## Example Usage

### JavaScript/Fetch API

```javascript
// Register a new user
const registerUser = async (userData) => {
    const response = await fetch('/api/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(userData)
    });
    return response.json();
};

// Login
const loginUser = async (username, password) => {
    const response = await fetch('/api/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ username, password })
    });
    return response.json();
};

// Get user info
const getUserInfo = async () => {
    const response = await fetch('/api/user/', {
        method: 'GET',
        credentials: 'same-origin'
    });
    return response.json();
};
```

### cURL Examples

```bash
# Register
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password1":"securepass123","password2":"securepass123"}'

# Login
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"securepass123"}'

# Get user info (with session)
curl -X GET http://localhost:8000/api/user/ \
  -H "Cookie: sessionid=your_session_id"
```

## Environment Configuration

For production deployment as auth.szlg.info, configure these environment variables:

```env
# Security
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=auth.szlg.info,localhost

# SSL/Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# CORS
CORS_ALLOWED_ORIGINS=https://yourapp.com,https://anotherapp.com

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/auth_db

# Redis
REDIS_URL=redis://localhost:6379
```