from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import json
from llm import chat_with_diet_agent  

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
# POST /chat
# ---------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # Get response from AI agent
        response = chat_with_diet_agent(request.message, request.user_id)

        # Store the response in DB
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO diet (AI_Plan, user_id) VALUES (?, ?)", (response, request.user_id))
        conn.commit()
        conn.close()

        return {
            "user_message": request.message,
            "ai_response": json.loads(response),  # Assuming it's JSON string
            "status": "Stored in diet table"
        }
    except json.JSONDecodeError:
        return {
            "error": "AI response was not in valid JSON format.",
            "raw_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))