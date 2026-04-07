import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Find Robert Thompson's orders
cur.execute("SELECT id, order_number, email, name, status, total_amount, total_cents, created_at FROM orders WHERE LOWER(name) LIKE '%robert%' OR LOWER(email) LIKE '%thompson%' ORDER BY created_at DESC")
print("\n=== Robert Thompson's Orders ===\n")
for row in cur.fetchall():
    print(f"Order ID: {row[0]}")
    print(f"Order #: {row[1]}")
    print(f"Status: {row[4]}")
    print(f"Email: {row[2]}")
    print(f"Total: ${row[5]/100:.2f}")
    print(f"Created: {row[7]}")
    print()

cur.close()
conn.close()
