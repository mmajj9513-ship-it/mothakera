import sqlite3

DB_NAME = "mothakera.db"


def connect():
    return sqlite3.connect(DB_NAME)


def setup_database():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            teacher TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            piece_id TEXT,
            score INTEGER,
            mistakes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            word_wrong TEXT,
            word_correct TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


def user_exists(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    db.close()

    return result is not None


def save_user(user_id, name, teacher):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (user_id, name, teacher)
        VALUES (?, ?, ?)
    """, (user_id, name, teacher))

    db.commit()
    db.close()


def get_users():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT user_id, name, teacher
        FROM users
        ORDER BY name
    """)

    result = cursor.fetchall()

    db.close()

    return result


def get_user_count():
    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")

    result = cursor.fetchone()[0]

    db.close()

    return result


def save_attempt(user_id, piece_id, score, mistakes):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO attempts
        (user_id, piece_id, score, mistakes)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        piece_id,
        score,
        mistakes
    ))

    db.commit()
    db.close()


def save_mistake(user_id, wrong, correct):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO mistakes
        (user_id, word_wrong, word_correct)
        VALUES (?, ?, ?)
    """, (
        user_id,
        wrong,
        correct
    ))

    db.commit()
    db.close()


def get_statistics(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            MAX(score),
            AVG(score)
        FROM attempts
        WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()

    db.close()

    attempts = result[0] or 0
    highest = result[1] or 0
    average = round(result[2] or 0)

    return attempts, highest, average


def get_common_mistakes(user_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            word_wrong,
            word_correct,
            COUNT(*) AS total
        FROM mistakes
        WHERE user_id = ?
        GROUP BY word_wrong, word_correct
        ORDER BY total DESC
        LIMIT 10
    """, (user_id,))

    result = cursor.fetchall()

    db.close()

    return result