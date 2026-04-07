#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("Adding failure_reason column if not exists...")
    cur.execute("""
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS failure_reason TEXT DEFAULT '';
    """)
    conn.commit()
    print("✓ Column added successfully")
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
