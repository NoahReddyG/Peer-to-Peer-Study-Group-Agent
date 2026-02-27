import math
import logging
import numpy as np
from typing import List
from collections import defaultdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans

# --- 1. CONFIGURATION & LOGGING ---
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

# --- 2. DATA MODELS (THE BOUNCER) ---
class Student(BaseModel):
    name: str
    skill: int = Field(ge=1, le=5, description="Skill rating from 1 to 5")
    weakness: int = Field(ge=1, le=5, description="Weakness rating from 1 to 5")

class GroupRequest(BaseModel):
    students: List[Student]
    group_size: int = Field(default=3, gt=0, description="Desired members per group")

# --- 3. CORE ALGORITHM (THE BRAIN) ---
def generate_groups(student_data: list, group_size: int):
    # Sanity Checks
    if not student_data:
        logger.warning("Empty student list received.")
        return {"groups": []}
    
    if group_size <= 0:
        logger.error(f"Invalid group_size: {group_size}")
        raise ValueError("Group size must be greater than 0.")

    sorted_students = sorted(
        student_data, 
        key=lambda s: (s["skill"], s["weakness"]), 
        reverse=True
    )

    num_students = len(sorted_students)
    num_groups = max(1, math.ceil(num_students / group_size))
    
    group_map = defaultdict(list)
    
    group_idx = 0
    step = 1  
    
    for student in sorted_students:
        group_map[group_idx].append(student)
        
        group_idx += step
        
        if group_idx >= num_groups:
            group_idx = num_groups - 1  
            step = -1                   
        elif group_idx < 0:
            group_idx = 0               
            step = 1                    

    result_groups = []
    for c_id, members in group_map.items():
        avg_s = sum(m['skill'] for m in members) / len(members)
        result_groups.append({
            "group_id": int(c_id + 1),
            "members": members,
            "stats": {
                "member_count": len(members),
                "avg_skill": round(avg_s, 2)
            }
        })

    return {"groups": result_groups}

# --- 4. API ENDPOINTS ---
@app.get("/api/health")
async def health_check():
    return {"status": "Brain is online 🧠", "version": "1.1"}

@app.post("/api/cluster")
async def cluster_students(request: GroupRequest):
    try:
        student_dicts = [s.dict() for s in request.students]
        
        result = generate_groups(student_dicts, request.group_size)
        return result
        
    except ValueError as ve:
        logger.error(f"Validation Error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected system error: {e}")
        raise HTTPException(status_code=500, detail="Internal Algorithm Error")

# To run this: uvicorn filename:app --reload