import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("\n=== DELETING PENDING ORDERS ===\n")

# Get order IDs
pending_order_ids = []
cur.execute("SELECT id, order_number, email FROM orders WHERE status = 'pending'")
rows = cur.fetchall()

for row in rows:
    pending_order_ids.append(row[0])
    print(f"Deleting order {row[1]} (ID {row[0]}) from {row[2]}")

# Get item quantities before delete
cur.execute("""
SELECT ticket_tier_id, SUM(qty) as total_qty
FROM order_items
WHERE order_id = ANY(%s)
GROUP BY ticket_tier_id
""", (pending_order_ids,))

restore_list = cur.fetchall()
print(f"\nRestoring inventory:")
for tier_id, qty in restore_list:
    cur.execute("SELECT name FROM ticket_tiers WHERE id = %s", (tier_id,))
    tier_name = cur.fetchone()[0]
    print(f"  {tier_name}: -{qty} tickets (from sold count)")

# Delete order items
cur.execute("DELETE FROM order_items WHERE order_id = ANY(%s)", (pending_order_ids,))
print(f"\nDeleted {cur.rowcount} order items")

# Delete orders
cur.execute("DELETE FROM orders WHERE id = ANY(%s)", (pending_order_ids,))
print(f"Deleted {cur.rowcount} orders")

# Restore inventory (subtract qty from sold)
for tier_id, qty in restore_list:
    cur.execute("UPDATE ticket_tiers SET sold = sold - %s WHERE id = %s", (qty, tier_id))

conn.commit()

# Verify
print("\n=== VERIFICATION ===\n")
cur.execute("SELECT name, sold, capacity FROM ticket_tiers WHERE active = TRUE ORDER BY id")
print("Updated inventory:")
for row in cur.fetchall():
    avail = row[2] - row[1]
    print(f"  {row[0]}: {row[1]} sold / {row[2]} capacity ({avail} available)")

cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
completed = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
pending = cur.fetchone()[0]
print(f"\nOrders: {completed} completed, {pending} pending")

cur.close()
conn.close()

print("\n✓ Cleanup complete!")
