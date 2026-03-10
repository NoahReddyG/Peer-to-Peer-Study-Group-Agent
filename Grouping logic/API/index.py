import math
import logging
from typing import List, Dict
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --------------------------------------------------
# 1. CONFIGURATION & LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Peer-to-Peer Study Group API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 2. DATA MODELS
# --------------------------------------------------
class Subject(BaseModel):
    skill: int = Field(ge=1, le=5)
    weakness: int = Field(ge=1, le=5)

class Student(BaseModel):
    name: str
    subjects: Dict[str, Subject]

class GroupRequest(BaseModel):
    students: List[Student]
    group_size: int = Field(default=3, gt=0)

# --------------------------------------------------
# 3. COMPATIBILITY SCORING
# --------------------------------------------------
def compatibility_score(student, group):
    score = 0

    for subject, s_data in student["subjects"].items():
        student_weakness = s_data["weakness"]

        group_max_skill = max(
            (member["subjects"][subject]["skill"] for member in group),
            default=0
        )

        if student_weakness >= 4 and group_max_skill >= 4:
            score += 2
        elif group_max_skill >= student_weakness:
            score += 1

    return score

# --------------------------------------------------
# 4. CORE GROUPING ALGORITHM
# --------------------------------------------------
def generate_groups(student_data: list, group_size: int):
    if not student_data:
        return {"groups": []}

    if group_size <= 0:
        raise ValueError("Group size must be greater than 0")

    num_students = len(student_data)
    num_groups = max(1, math.ceil(num_students / group_size))

    groups = [[] for _ in range(num_groups)]

    for student in student_data:
        best_group_idx = None
        best_score = -1

        for idx, group in enumerate(groups):
            if len(group) >= group_size:
                continue

            score = compatibility_score(student, group)

            if score > best_score:
                best_score = score
                best_group_idx = idx

        if best_group_idx is None:
            best_group_idx = min(range(num_groups), key=lambda i: len(groups[i]))

        groups[best_group_idx].append(student)

    result = []
    for i, members in enumerate(groups):
        result.append({
            "group_id": i + 1,
            "members": members,
            "stats": {
                "member_count": len(members)
            }
        })

    return {"groups": result}

# --------------------------------------------------
# 5. API ENDPOINTS
# --------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "Brain is online 🧠", "version": "2.0"}

@app.post("/api/cluster")
async def cluster_students(request: GroupRequest):
    try:
        student_dicts = [s.dict() for s in request.students]
        return generate_groups(student_dicts, request.group_size)

    except ValueError as ve:
        logger.error(ve)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal Algorithm Error")

# --------------------------------------------------
# Run with:
# uvicorn filename:app --reload
# --------------------------------------------------