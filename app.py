from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
from clustering import generate_groups

app = FastAPI(title="Peer-to-Peer Study Group API")

# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = 'database.db'

class Student(BaseModel):
    name: str
    skill: int
    weakness: int

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
            skill INTEGER NOT NULL, 
            weakness INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/add_student")
async def add_student(student: Student):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO students (name, skill, weakness) VALUES (?, ?, ?)',
        (student.name, student.skill, student.weakness)
    )
    conn.commit()
    conn.close()
    return {"message": "Student added successfully"}

@app.get("/get_students")
async def get_students():
    conn = get_db()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    return [dict(ix) for ix in students]

@app.post("/generate_groups")
async def generate():
    conn = get_db()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    
    student_list = [dict(ix) for ix in students]
    if not student_list:
        raise HTTPException(status_code=400, detail="No students found to group")
        
    groups = generate_groups(student_list)
    return {
        "status": "success",
        "groups": groups
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
