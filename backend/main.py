""" Main application file for the FastAPI backend. Handles API endpoints and integrates with the LLM and database modules. """
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm import get_structured_output, store_response, get_user_data
from db import supabase

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# Chat Request Body
class ChatRequest(BaseModel):
    """ Pydantic model for the request body of the /health_ai endpoint. """
    message: str
    user_id: int


class GoogleAuthRequest(BaseModel):
    """Pydantic model for Google-style login/signup bootstrap."""
    email: str
    name: str | None = None


class UserProfileUpdateRequest(BaseModel):
    """Pydantic model for updating user profile metrics."""
    user_id: int
    height: float
    weight: float
    age: int
    gender: str
    bfp: float | None = None


def profile_is_complete(row: dict) -> bool:
    """Returns True when all required profile fields are available."""
    required_fields = ["height", "weight", "age", "gender", "bfp"]
    return all(row.get(field) is not None for field in required_fields)


# ---------------------------
# POST /auth/google - Create or fetch user by email
# ---------------------------
@app.post("/auth/google")
def auth_google(request: GoogleAuthRequest):
    """Create or fetch a user account using Google email identity."""
    email = request.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing = supabase.table("user").select("*").eq("email", email).limit(1).execute()
    if existing.data and len(existing.data) > 0:
        row = existing.data[0]
        return {
            "user": {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "height": row.get("height"),
                "weight": row.get("weight"),
                "age": row.get("age"),
                "gender": row.get("gender"),
                "bfp": row.get("bfp"),
            },
            "profile_complete": profile_is_complete(row),
            "is_new_user": False,
        }

    insert_payload = {
        "name": request.name.strip() if request.name else email.split("@")[0],
        "email": email,
        "height": None,
        "weight": None,
        "age": None,
        "gender": None,
        "bfp": None,
    }

    created = supabase.table("user").insert([insert_payload]).execute()
    if not created.data or len(created.data) == 0:
        raise HTTPException(status_code=500, detail="Could not create user")

    row = created.data[0]
    return {
        "user": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "height": row.get("height"),
            "weight": row.get("weight"),
            "age": row.get("age"),
            "gender": row.get("gender"),
            "bfp": row.get("bfp"),
        },
        "profile_complete": False,
        "is_new_user": True,
    }


# ---------------------------
# POST /user/profile - Update profile fields
# ---------------------------
@app.post("/user/profile")
def update_user_profile(request: UserProfileUpdateRequest):
    """Update user profile data required by AI planning."""
    update_payload = {
        "height": request.height,
        "weight": request.weight,
        "age": request.age,
        "gender": request.gender,
        "bfp": request.bfp,
    }

    updated = (
        supabase.table("user")
        .update(update_payload)
        .eq("id", request.user_id)
        .execute()
    )

    if not updated.data or len(updated.data) == 0:
        raise HTTPException(status_code=404, detail="User not found")

    row = updated.data[0]
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "height": row.get("height"),
            "weight": row.get("weight"),
            "age": row.get("age"),
            "gender": row.get("gender"),
            "bfp": row.get("bfp"),
        },
        "profile_complete": profile_is_complete(row),
    }


# ---------------------------
# GET /user?id=
# ---------------------------
@app.get("/user")
def get_user(user_id: int = Query(..., description="User ID")):
    """ Fetch user data from the database for a given user ID. """
    response = supabase.table("user").select("*").eq("id", user_id).execute()
    data = response.data

    if data and len(data) > 0:
        row = data[0]
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "height": row["height"],
            "weight": row["weight"],
            "age": row["age"],
            "gender": row["gender"],
            "bfp": row.get("bfp"),
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")


# ---------------------------
# GET /diets - Get all diets
# ---------------------------
@app.get("/diets")
def get_all_diets():
    """ Fetch all diet plans from the database. """
    response = supabase.table("diet").select("*").execute()
    rows = response.data

    diets = []
    for row in rows:
        try:
            ai_plan = (
                json.loads(row["AI_Plan"])
                if row["AI_Plan"] and isinstance(row["AI_Plan"], str)
                else row["AI_Plan"]
            )
        except json.JSONDecodeError:
            ai_plan = row["AI_Plan"]  # if it wasn't valid JSON, return as raw string

        diets.append({"id": row["id"], "AI_Plan": ai_plan, "user_id": row["user_id"]})

    return diets


# ---------------------------
# GET /diet?id=
# ---------------------------
@app.get("/diet")
def get_diet(diet_id: int = Query(..., description="Diet ID")):
    """ Fetch a specific diet plan from the database by its ID. """
    response = supabase.table("diet").select("*").eq("id", diet_id).execute()
    data = response.data

    if data and len(data) > 0:
        row = data[0]
        try:
            ai_plan = (
                json.loads(row["AI_Plan"])
                if row["AI_Plan"] and isinstance(row["AI_Plan"], str)
                else row["AI_Plan"]
            )
        except json.JSONDecodeError:
            ai_plan = row["AI_Plan"]  # if it wasn't valid JSON, return as raw string

        return {"id": row["id"], "AI_Plan": ai_plan, "user_id": row["user_id"]}
    else:
        raise HTTPException(status_code=404, detail="Diet not found")


# ---------------------------
# POST /health_ai - Combined endpoint for diet plans and meal logging
# ---------------------------
@app.post("/health_ai")
def health_ai(request: ChatRequest):
    """ Main endpoint to handle user queries for diet planning and meal logging. """
    try:
        user_id = request.user_id
        user_prompt = request.message
        user_data = get_user_data(user_id)
        response = get_structured_output(user_prompt, user_data)
        if response["response_type"] == "diet_plan":
            store_response(user_id, response)
            return {"message": response["message"], "diet_plan": response["diet_plan"]}
        elif response["response_type"] == "meal_logging":
            meal_type = response["mealType"]
            user_meals = response["items"]
            store_response(user_id, response)
            return {
                "message": response["message"],
                "meal_log": {"meal_type": meal_type, "user_meals": user_meals},
            }
        elif response["response_type"] == "conversation":
            return {"message": response["message"]}
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid request_type. Must be 'diet_plan' or 'meal_log'",
            )

    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON") from je

    except ValueError as ve:
        # This is for missing user in DB
        raise HTTPException(status_code=404, detail=str(ve)) from ve

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e
