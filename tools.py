import sqlite3
from langchain.agents import Tool

# ---------- Database Config ----------
DB_NAME = "health_tracker.db"

def fetch_user_info_from_db(user_id: int) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT height, weight, age, gender, bfp FROM user WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return f"""
        User Information:
        - Height: {row[0]} cm
        - Weight: {row[1]} kg
        - Age: {row[2]}
        - Gender: {row[3]}
        - Body Fat Percentage: {row[4]}
        """
    else:
        raise ValueError(f"No user found with ID {user_id}")

# ---------- LangChain Tool ----------
def get_user_info_tool(_: str, user_id: int = 1) -> str:
    return fetch_user_info_from_db(user_id)

# Tool definition
def create_user_tool(user_id: int):
    return Tool(
        name="GetUserProfile",
        func=lambda x: get_user_info_tool(x, user_id=user_id),
        description="Provides the user's height, weight, age, gender, and body fat percentage"
    )