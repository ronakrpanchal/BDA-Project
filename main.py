from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import json
from llm import get_structured_output , get_user_data , store_AI_plan
from typing import Dict

app = FastAPI()

DB_NAME = 'health_tracker.db'

# Chat Request Body
class ChatRequest(BaseModel):
    message: str
    user_id: int
    
class MealLog(BaseModel):
    user_id: int
    meal_type: str
    user_meals: Dict

# ---------------------------
# GET /user?id=
# ---------------------------
@app.get("/user")
def get_user(id: int = Query(..., description="User ID")):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "height": row[3],
            "weight": row[4],
            "age": row[5],
            "gender": row[6],
            "bfp": row[7]
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")

# ---------------------------
# GET /diet?id=
# ---------------------------
@app.get("/diet")
def get_diet(id: int = Query(..., description="Diet ID")):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diet WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        try:
            ai_plan = json.loads(row[1]) if row[1] else None
        except json.JSONDecodeError:
            ai_plan = row[1]  # if it wasn't valid JSON, return as raw string

        return {
            "id": row[0],
            "AI_Plan": ai_plan,
            "user_id": row[2]
        }
    else:
        raise HTTPException(status_code=404, detail="Diet not found")

# ---------------------------
# POST /chat
# ---------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # Step 1: Fetch user data from DB
        user_data = get_user_data(request.user_id)

        # Step 2: Get structured response from Groq (LLaMA)
        structured_plan = get_structured_output(request.message, user_data)

        # Step 3: Store the structured JSON response into the database
        store_AI_plan(request.user_id, json.dumps(structured_plan))  # serialize dict to JSON string

        # Step 4: Return a clean response
        return {
            "user_message": request.message,
            "ai_response": structured_plan,
            "status": "Stored in diet table"
        }

    except ValueError as ve:
        # This is for missing user in DB
        raise HTTPException(status_code=404, detail=str(ve))

    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
@app.post("/meal_log")
def meal_log(request: MealLog):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    user_meals_json = json.dumps(request.user_meals)  # Convert dict to JSON string
    
    # Assuming meal_log table has columns: id, user_id, meal_type, user_meals
    cursor.execute(
        "INSERT INTO meal_log (user_id, meal_type, user_meals) VALUES (?, ?, ?)",
        (request.user_id, request.meal_type, user_meals_json)
    )
    
    conn.commit()
    conn.close()
    
    return {"status": "Meal log stored successfully"}