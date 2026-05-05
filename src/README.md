# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher login/logout with backend credential validation
- Teacher-only sign up and unregister actions

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student from an activity                               |
| POST   | `/auth/login`                                                     | Log in teacher and create a session cookie                          |
| POST   | `/auth/logout`                                                    | Log out teacher and clear session cookie                            |
| GET    | `/auth/me`                                                        | Get current teacher auth status                                     |

## Teacher Credentials

Teacher credentials are loaded from a local untracked file and validated by the backend.

Create this file before starting the app:

- Path: `src/.local/teachers.local.json`
- Schema:

   ```json
   {
      "teachers": [
         {
            "username": "teacher-username",
            "password_hash": "sha256-hash"
         }
      ]
   }
   ```

You can also set `TEACHERS_FILE_PATH` to point to a different local credentials file.

When this app is hosted later, teacher credentials should be moved to a secure database-backed auth flow.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
