"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json
import secrets
import hashlib
import hmac
from pathlib import Path
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


class LoginRequest(BaseModel):
    username: str
    password: str

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

teacher_sessions = {}


def load_teacher_credentials():
    configured_path = os.getenv("TEACHERS_FILE_PATH")
    credentials_path = Path(configured_path) if configured_path else current_dir / ".local" / "teachers.local.json"

    if not credentials_path.exists():
        raise RuntimeError(
            "Teacher credentials file was not found. "
            "Create src/.local/teachers.local.json or set TEACHERS_FILE_PATH."
        )

    with credentials_path.open("r", encoding="utf-8") as credentials_file:
        data = json.load(credentials_file)

    teachers = {}
    for teacher in data.get("teachers", []):
        username = teacher.get("username")
        password_hash = teacher.get("password_hash")
        if username and password_hash:
            teachers[username] = password_hash
    return teachers


TEACHERS = load_teacher_credentials()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_teacher(username: str, password: str):
    stored_hash = TEACHERS.get(username)
    if not stored_hash:
        return False
    return hmac.compare_digest(stored_hash, hash_password(password))


def require_teacher(teacher_session: str | None = Cookie(default=None)):
    if not teacher_session:
        raise HTTPException(status_code=403, detail="Teacher login required")

    username = teacher_sessions.get(teacher_session)
    if not username:
        raise HTTPException(status_code=403, detail="Teacher login required")

    return username

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login_teacher(payload: LoginRequest, response: Response):
    if not authenticate_teacher(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    teacher_sessions[session_token] = payload.username
    response.set_cookie(
        key="teacher_session",
        value=session_token,
        httponly=True,
        samesite="lax"
    )
    return {"message": "Logged in successfully", "username": payload.username}


@app.post("/auth/logout")
def logout_teacher(response: Response, teacher_session: str | None = Cookie(default=None)):
    if teacher_session:
        teacher_sessions.pop(teacher_session, None)
    response.delete_cookie("teacher_session")
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def get_auth_status(teacher_session: str | None = Cookie(default=None)):
    username = teacher_sessions.get(teacher_session) if teacher_session else None
    return {
        "authenticated": bool(username),
        "username": username
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher: str = Depends(require_teacher)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher: str = Depends(require_teacher)):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
