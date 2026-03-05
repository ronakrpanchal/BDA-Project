from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import json
from llm import get_structured_output, store_response , get_user_data

app = FastAPI()

DB_NAME = 'health_tracker.db'

# Chat Request Body
class ChatRequest(BaseModel):
    message: str
    user_id: int

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
# POST /health_ai - Combined endpoint for diet plans and meal logging
# ---------------------------
@app.post("/health_ai")
def health_ai(request: ChatRequest):
    try:
        user_id = request.user_id
        user_prompt = request.message
        user_data = get_user_data(user_id)
        response = get_structured_output(user_prompt, user_data)
        if response["response_type"] == "diet_plan":
            store_response(user_id, response)
            return {
                "message": response["message"],
                "diet_plan": response["diet_plan"]
            }
        elif response["response_type"] == "meal_logging":
            meal_type = response["mealType"]
            user_meals = response["items"]
            store_response(user_id, response)
            return {
                "message": response["message"],
                "meal_log": {
                    "meal_type": meal_type,
                    "user_meals": user_meals
                }
            }
        elif response["response_type"] == "conversation":
            return {
                "message": response["message"]
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid request_type. Must be 'diet_plan' or 'meal_log'")

    except ValueError as ve:
        # This is for missing user in DB
        raise HTTPException(status_code=404, detail=str(ve))

    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")