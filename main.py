from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import json
from llm import get_structured_output , get_user_data , store_AI_plan, meal_logging, store_meal
from typing import Dict
from kafka import KafkaProducer
from json import dumps
import datetime
import os

app = FastAPI()

DB_NAME = 'health_tracker.db'

# Configure Kafka Producer
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC_MEAL_LOGS = 'meal-logs'

try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=lambda x: dumps(x).encode('utf-8')
    )
    print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    print(f"Failed to connect to Kafka: {e}")
    producer = None

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
def meal_log(request: ChatRequest):
    try:
        meal_plan = meal_logging(request.message)
        print("\n--- Meal Logging Output ---\n")
        # print(json.dumps(meal_plan, indent=2))
        store_meal(request.user_id, meal_plan['mealType'], json.dumps(meal_plan))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging meal: {e}")
    
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    # Send meal log data to Kafka for real-time processing
    if producer:
        try:
            # Prepare data for Kafka
            kafka_data = {
                # "id": meal_log_id,
                "user_id": request.user_id,
                "meal_type": request.meal_type,
                "user_meals": request.user_meals,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Send data to Kafka topic
            producer.send(KAFKA_TOPIC_MEAL_LOGS, value=kafka_data)
            producer.flush()  # Ensure data is sent
            print(f"Sent meal log data to Kafka topic {KAFKA_TOPIC_MEAL_LOGS}")
        except Exception as e:
            print(f"Failed to send data to Kafka: {e}")
    
    return {"status": "Meal log stored successfully"}