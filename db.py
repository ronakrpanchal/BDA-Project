import sqlite3

conn = sqlite3.connect('health_tracker.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        height REAL,
        weight REAL,
        age INTEGER,
        gender TEXT,
        bfp REAL  -- Body Fat Percentage
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS diet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        AI_Plan TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
''')

conn.commit()
conn.close()