"""
database.py - Простые операции с SQLite для хранения жалоб
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

DB_NAME = "complaints.db"


def init_db():
    """Создание таблицы в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sentiment TEXT,
            category TEXT DEFAULT 'другое'
        )
    """)

    conn.commit()
    conn.close()


def create_complaint(text: str, sentiment: str, category: str = "другое") -> int:
    """Создание новой жалобы"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints (text, sentiment, category)
        VALUES (?, ?, ?)
    """, (text, sentiment, category))

    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return complaint_id


def get_complaints(filters: Dict) -> List[Dict]:
    """Получение жалоб с фильтрами"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if "status" in filters:
        query += " AND status = ?"
        params.append(filters["status"])

    if "since" in filters:
        query += " AND timestamp > ?"
        params.append(filters["since"].strftime("%Y-%m-%d %H:%M:%S"))

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Преобразуем в словари
    complaints = []
    for row in rows:
        complaints.append({
            "id": row[0],
            "text": row[1],
            "status": row[2],
            "timestamp": row[3],
            "sentiment": row[4],
            "category": row[5]
        })

    conn.close()
    return complaints


def update_complaint_status(complaint_id: int, status: str) -> bool:
    """Обновление статуса жалобы"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def update_complaint_category(complaint_id: int, category: str) -> bool:
    """Обновление категории жалобы (для AI)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET category = ?
        WHERE id = ?
    """, (category, complaint_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def get_complaint_by_id(complaint_id: int) -> Optional[Dict]:
    """Получение жалобы по ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()

    if row:
        complaint = {
            "id": row[0],
            "text": row[1],
            "status": row[2],
            "timestamp": row[3],
            "sentiment": row[4],
            "category": row[5]
        }
    else:
        complaint = None

    conn.close()
    return complaint