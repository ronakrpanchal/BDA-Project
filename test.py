import sqlite3

DB_NAME = "health_tracker.db"

def insert_demo_user():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Demo user data
    user_data = (
        1,                     # id
        "John Doe",            # name
        "john@example.com",    # email
        175.0,                 # height (cm)
        72.0,                  # weight (kg)
        28,                    # age
        "male",                # gender
        17.8                   # body fat percentage
    )

    cursor.execute("""
        INSERT OR REPLACE INTO user (id, name, email, height, weight, age, gender, bfp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, user_data)

    conn.commit()
    conn.close()
    print("✅ Demo user inserted successfully.")
    
    
def check_diet_db(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM diet where user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row[1] if row else None
    
def remove_user(userId):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM diet WHERE user_id = ?", (userId,))
    
    print(f"{userId} removed")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    insert_demo_user()
    # remove_user(1)
    # ai_plan=check_diet_db(1)
    
    # print(type(ai_plan))
    # print(len(ai_plan))
    # print(ai_plan)
    
    # js = json.loads(ai_plan)
    
    # print(type(js))
    
    # print(json.loads(ai_plan[:2500]))