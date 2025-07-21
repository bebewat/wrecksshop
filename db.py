import pymysql
import json

conn = pymysql.connect("shop.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    player_id TEXT,
    points INTEGER,
    status TEXT,
    source TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS pending_deliveries (
    id INTEGER PRIMARY KEY,
    player_id TEXT,
    item_name TEXT,
    command TEXT,
    map TEXT,
    price INTEGER,
    status TEXT DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def get_eos_for_discord(discord_id):
    return f"eos_{discord_id}"

def get_balance(player_id):
    c.execute("SELECT SUM(points) FROM transactions WHERE player_id = ?", (player_id,))
    r = c.fetchone()[0]
    return r or 0

def log_transaction(player_id, points, status, source="shop"):
    c.execute("INSERT INTO transactions (player_id, points, status, source) VALUES (?,?,?,?)",
              (player_id, points, status, source))
    conn.commit()
    return get_balance(player_id)

def queue_delivery(player_id, item_name, command, map_name, price):
    c.execute("INSERT INTO pending_deliveries (player_id, item_name, command, map, price) VALUES (?,?,?,?,?)",
              (player_id, item_name, command, map_name, price))
    conn.commit()

def deliver_queued_items():
    c.execute("SELECT id, player_id, command FROM pending_deliveries WHERE status='pending'")
    rows = c.fetchall(); count=0
    for id, pid, cmd in rows:
        # assume success
        c.execute("UPDATE pending_deliveries SET status='delivered' WHERE id=?", (id,))
        count+=1
    conn.commit()
    return count
