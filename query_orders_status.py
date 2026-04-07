import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# All orders by status
cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
print("\n=== Orders by Status ===\n")
for row in cur.fetchall():
    print(f"{row[0].upper()}: {row[1]} orders")

print("\n=== Pending & Failed Orders (not completed) ===\n")
cur.execute("SELECT id, order_number, email, name, status, total_amount, created_at FROM orders WHERE status IN ('pending', 'failed') ORDER BY created_at DESC")
for row in cur.fetchall():
    print(f"Order {row[1]} (ID {row[0]}): {row[4]} - {row[2]} - ${row[5]/100:.2f} - {row[6]}")

cur.close()
conn.close()
