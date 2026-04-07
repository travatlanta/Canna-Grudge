import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("\n=== INVENTORY IMPACT ===\n")
print("Pending orders and their item impact:\n")

# Get all pending order items
cur.execute("""
SELECT oi.id, oi.order_id, oi.tier_name, oi.qty, o.order_number, o.email
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
WHERE o.status = 'pending'
ORDER BY o.created_at
""")

total_held = 0
for row in cur.fetchall():
    print(f"Order {row[4]} ({row[5]}): {row[2]} x{row[3]}")
    total_held += row[3]

print(f"\nTotal tickets held in pending orders: {total_held}")

# Get current inventory
cur.execute("SELECT name, sold, capacity FROM ticket_tiers WHERE active = TRUE ORDER BY id")
print("\n=== CURRENT INVENTORY ===\n")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]} sold / {row[2]} capacity ({row[2]-row[1]} available)")

cur.close()
conn.close()
