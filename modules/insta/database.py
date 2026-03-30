"""
Database module for storing analysis history
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
import os

import tempfile

# Determine database path (handle Vercel read-only filesystem)
try:
    test_path = os.path.join(os.path.dirname(__file__), ".test_write")
    with open(test_path, "w") as f:
        f.write("test")
    os.remove(test_path)
    DB_PATH = os.path.join(os.path.dirname(__file__), "risk_detector.db")
except Exception:
    DB_PATH = os.path.join(tempfile.gettempdir(), "risk_detector.db")
    print(f"Running in read-only environment. Database path: {DB_PATH}")


def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            confidence_label TEXT NOT NULL,
            reasons TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")


def save_analysis(analysis_data: Dict[str, Any]):
    """Save an analysis to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO analyses 
        (username, risk_score, risk_level, confidence, confidence_label, reasons, recommendations, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_data["username"],
        analysis_data["risk_score"],
        analysis_data["risk_level"],
        analysis_data["confidence"],
        analysis_data["confidence_label"],
        json.dumps(analysis_data["reasons"]),
        json.dumps(analysis_data["recommendations"]),
        analysis_data["timestamp"]
    ))
    
    conn.commit()
    conn.close()


def get_recent_analyses(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent analyses from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, risk_score, risk_level, confidence, confidence_label, 
               reasons, recommendations, timestamp
        FROM analyses
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    analyses = []
    for row in rows:
        analyses.append({
            "username": row[0],
            "risk_score": row[1],
            "risk_level": row[2],
            "confidence": row[3],
            "confidence_label": row[4],
            "reasons": json.loads(row[5]),
            "recommendations": json.loads(row[6]),
            "timestamp": row[7]
        })
    
    return analyses
