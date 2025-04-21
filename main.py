from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import json
from llm import get_structured_output, store_response , get_user_data
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        print(je)
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    


@app.get("/diets")
def get_all_diets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diet")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        diets = []
        for row in rows:
            try:
                ai_plan = json.loads(row[1]) if row[1] else None
            except json.JSONDecodeError:
                ai_plan = row[1]  

            diets.append({
                "id": row[0],
                "AI_Plan": ai_plan,
                "user_id": row[2]
            })

        return diets
    else:
        return JSONResponse(content={"message": "No diets found"}, status_code=200)
    

@app.get("/logs")
def get_all_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meal_log")
    rows = cursor.fetchall()
    conn.close()
    print(rows)

    if rows:
        logs = []
        for row in rows:
            try:
                meal_data = json.loads(row[3]) if row[3] else None
            except json.JSONDecodeError:
                meal_data = row[3]

            logs.append({
                "id": row[0],
                "user_id": row[1],
                "meal_type": row[2],
                "meal_data": meal_data
            })
        return logs
    else:
        return JSONResponse(content={"message": "No logs found"}, status_code=200)



@app.delete("/logs/clear")
def clear_all_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meal_log")
    conn.commit()
    conn.close()
    return {"message": "All meal logs deleted"}
