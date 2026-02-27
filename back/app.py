from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import sqlite3
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta
import hashlib

from clustering import generate_groups
from mock_erp import MockERP

# ------------------ CONFIG ------------------

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE = "database.db"

app = FastAPI(title="Peer-to-Peer Study Group API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ MODELS ------------------

class StudentRegister(BaseModel):
    name: str
    roll_no: str
    password: str
    skill: int
    weakness: int

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str

# ------------------ UTILS ------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------ DATABASE ------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            skill INTEGER NOT NULL,
            weakness INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

# ------------------ AUTH DEPENDENCIES ------------------

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return User(username=username, role=role)

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# ------------------ ROUTES ------------------

# 🔐 Login (Admin + Student)
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()

    # 1️⃣ Admin Login via MockERP
    if MockERP.verify_admin(form_data.username, form_data.password):
        token = create_access_token(
            {"sub": form_data.username, "role": "admin"}
        )
        conn.close()
        return {"access_token": token, "token_type": "bearer"}

    # 2️⃣ Student Login via SQLite
    student = conn.execute(
        "SELECT * FROM students WHERE roll_no = ?",
        (form_data.username,)
    ).fetchone()

    if student and hash_password(form_data.password) == student["password"]:
        token = create_access_token(
            {"sub": student["roll_no"], "role": "student"}
        )
        conn.close()
        return {"access_token": token, "token_type": "bearer"}

    conn.close()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

# 📝 Student Registration (Frontend)
@app.post("/student/register")
async def register_student(student: StudentRegister):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO students (name, roll_no, password, skill, weakness) VALUES (?, ?, ?, ?, ?)",
            (
                student.name,
                student.roll_no,
                hash_password(student.password),
                student.skill,
                student.weakness,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Roll number already exists")
    finally:
        conn.close()

    return {"message": "Student registered successfully"}

# 👀 View Students
@app.get("/get_students")
async def get_students():
    conn = get_db()
    students = conn.execute(
        "SELECT id, name, roll_no, skill, weakness FROM students"
    ).fetchall()
    conn.close()

    return [dict(row) for row in students]

# 🤖 Generate Groups (Admin Only)
@app.post("/generate_groups", dependencies=[Depends(get_current_admin)])
async def generate():
    conn = get_db()
    students = conn.execute(
        "SELECT id, name, roll_no, skill, weakness FROM students"
    ).fetchall()
    conn.close()

    student_list = [dict(row) for row in students]

    if not student_list:
        raise HTTPException(status_code=400, detail="No students found")

    groups = generate_groups(student_list)

    return {
        "status": "success",
        "groups": groups
    }

# ------------------ RUN ------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
