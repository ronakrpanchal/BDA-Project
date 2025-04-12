import os
import sqlite3
import requests
import json
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "health_tracker.db"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ---------- Fetch User Data ----------
def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT height, weight, age, gender, bfp FROM user WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"No user found with ID {user_id}")
    return {
        "height": row[0],
        "weight": row[1],
        "age": row[2],
        "gender": row[3],
        "bfp": row[4]
    }

# ---------- Get Structured Response from Groq API ----------
def get_structured_output(user_prompt, user_data):
    system_prompt = f"""
You are a professional **diet planning assistant**.

Your task is to return **only a valid JSON response** that strictly follows the schema given below. No explanations, no extra text—just clean, valid JSON.

---

### 📄 Schema (Strict Format):
{{
  "dailyNutrition": {{
    "calories": 1850,
    "carbs": 260,
    "fats": 55,
    "protein": 110,
    "waterIntake": "4 liters"
  }},
  "calorieDistribution": [
    {{ "category": "carbohydrates", "percentage": "50%" }},
    {{ "category": "proteins", "percentage": "30%" }},
    {{ "category": "fats", "percentage": "20%" }}
  ],
  "goal": "<User goal here (e.g., fat loss)>",
  "dietPreference": "<User diet preference (e.g., vegetarian, vegan)>",
  "workoutRoutine": [
    {{ "day": "Monday", "routine": "Cardio - 30 minutes" }},
    {{ "day": "Tuesday", "routine": "Strength - 30 minutes" }},
    {{ "day": "Wednesday", "routine": "Yoga - 30 minutes" }},
    {{ "day": "Thursday", "routine": "Cycling - 45 minutes" }},
    {{ "day": "Friday", "routine": "HIIT - 20 minutes" }},
    {{ "day": "Saturday", "routine": "Walk - 60 minutes" }},
    {{ "day": "Sunday", "routine": "Rest or light stretching" }}
  ],
  "mealPlans": [
    {{
      "day": "Monday",
      "totalCalories": 2200,
      "macronutrients": {{
        "carbohydrates": 275,
        "proteins": 165,
        "fats": 49
      }},
      "meals": [
        {{
          "mealType": "breakfast",
          "items": [
            {{
              "name": "Idli with Sambhar",
              "ingredients": ["rawa", "tomatoes", "dal", "spices", "onions"],
              "calories": 350
            }},
            ...
          ]
        }},
        ...
      ]
    }},
    ... (Repeat for other days up to Sunday)
  ]
}}

---

### 📌 Data Input Instructions:

Some user info is fetched from the database, the rest is extracted from the prompt.

- **Database Data** (already provided to you):
  - Height: {user_data['height']} cm
  - Weight: {user_data['weight']} kg
  - Age: {user_data['age']} years
  - Gender: {user_data['gender']}
  - Body Fat Percentage (BFP): {user_data['bfp']}%

- **Prompt Data** (user will provide in prompt):
  - Goal (e.g., weight loss, muscle gain)
  - Budget (if any)
  - Allergies or medical conditions (if mentioned)
  - Calorie intake (if specified)
  - Activity level (e.g., sedentary, high)

---

### 🍽️ Meal Planning Guidelines:

- Meals must be Indian/Gujarati style.
- For vegetarians: strictly avoid non-veg.
- For vegans: strictly avoid non-veg and dairy.
- Account for user allergies and medical conditions (if mentioned).
- All meals must mention calories and include ingredients using regional items.
- Ensure 7-day plan follows calorie and macronutrient targets.
- Do not output any units for integers (e.g., 275 not "275g").

---

### ⚠️ Important:

- **DO NOT include any extra commentary or markdown.**
- **Output must be a valid JSON structure as shown above.**
- avoid backticks and writing json 
"""

    payload = {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "temperature": 0.5,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(GROQ_ENDPOINT, headers=HEADERS, json=payload)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("Failed to parse JSON. Raw content:\n", content)
        raise

# ---------- Store in DB ----------
def store_AI_plan(user_id: int, ai_json: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO diet (user_id, AI_plan) VALUES (?, ?)",
        (user_id, ai_json)
    )
    conn.commit()
    conn.close()

# ---------- Main ----------
if __name__ == "__main__":
    user_id = 1
    user_prompt = "Can you plan a budget-friendly high-protein vegetarian diet for me?"

    try:
        user_data = get_user_data(user_id)
        structured_plan = get_structured_output(user_prompt, user_data)

        print("\n--- AI Structured Output ---\n")
        print(json.dumps(structured_plan, indent=2))

        # Optional: Save to DB
        store_AI_plan(user_id, json.dumps(structured_plan))
        print("Plan saved successfully.")
    except Exception as e:
        print(f"Error: {e}")