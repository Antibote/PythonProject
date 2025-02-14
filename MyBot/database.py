import sqlite3
from config import DB_PATH

def db_execute(query, params=()):
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()
            print(f"Выполняю запрос: {query} с параметрами: {params}")  # Логирование
            cur.execute(query, params)
            conn.commit()
            if query.strip().upper().startswith("INSERT"):
                print(f"Успешно. Последний ID: {cur.lastrowid}")  # Логирование
                return cur.lastrowid
            print("Успешно выполнен запрос.")  # Логирование
            return True
    except sqlite3.Error as e:
        print(f"Ошибка БД2: {e}")
        return False

def db_fetchall(query, params=()):
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Ошибка БД1: {e}")
        return []

def db_setup():
    db_execute("""
    CREATE TABLE IF NOT EXISTS Adds (
        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        ChatID INTEGER NOT NULL,  
        Task TEXT NOT NULL 
    )
    """)
    db_execute("""
    CREATE TABLE IF NOT EXISTS Reminders (
        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        TaskID INTEGER NOT NULL,
        ReminderTime TEXT NOT NULL, 
        FOREIGN KEY (TaskID) REFERENCES Adds(Id)
    )
    """)