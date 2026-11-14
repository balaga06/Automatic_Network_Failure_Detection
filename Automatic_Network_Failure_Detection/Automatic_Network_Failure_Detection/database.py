import sqlite3
from datetime import datetime

DB_NAME = "network_monitor.db"


# -------------------------------
# Database Connection
# -------------------------------

import os



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "network_monitor.db")
print("DATABASE PATH:", DB_PATH)

def get_connection():
      # DEBUG LINE

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# Create Tables
# -------------------------------
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Nodes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        node_type TEXT NOT NULL,          -- ISP | CORE | VLAN | LOGICAL
        ip_address TEXT,                  -- NULL for logical nodes
        parent_id INTEGER,
        is_pingable INTEGER NOT NULL,     -- 1 = yes, 0 = no
        is_active INTEGER DEFAULT 1
    )
    """)

    # 2. Current monitoring status
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS monitoring_status (
    node_id INTEGER PRIMARY KEY,
    status TEXT,
    latency_ms REAL,
    last_updated TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
     )
       """)

    # 3. Status history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id INTEGER,
        checked_at TEXT,
        latency_ms REAL,
        status TEXT
    )
    """)

    # 4. Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id INTEGER,
        alert_type TEXT,
        alert_time TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()

def create_topology_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS network_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_ip TEXT,
        destination_ip TEXT,
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
# -------------------------------
# Initialize Database
# -------------------------------
def init_database():
    create_tables()
    create_topology_table()   
    print("Database initialized successfully.")


# -------------------------------
# Run directly
# -------------------------------

from network_config import (
    ISP_LINKS,
    CORE_SERVER,
    VLAN_GATEWAYS,
    LOGICAL_BLOCKS,
    NODE_IPS
)

# ----------------------------------
# Insert Node Helper
# ----------------------------------

def insert_node(name, node_type, ip_address, parent_id, is_pingable):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nodes (name, node_type, ip_address, parent_id, is_pingable)
        VALUES (?, ?, ?, ?, ?)
    """, (name, node_type, ip_address, parent_id, is_pingable))

    conn.commit()
    node_id = cursor.lastrowid
    conn.close()
    return node_id


# ----------------------------------
# Populate All Network Nodes
# ----------------------------------

def populate_nodes():
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data (safe for development)
    cursor.execute("DELETE FROM alerts")
    cursor.execute("DELETE FROM status_history")
    cursor.execute("DELETE FROM monitoring_status")
    cursor.execute("DELETE FROM nodes")
    conn.commit()
    conn.close()

    node_ids = {}

    # 3. Virtual Internet Service Node
    internet_service_id = insert_node(
        name="INTERNET_SERVICE",
        node_type="SERVICE",
        ip_address=None,
        parent_id=None,
        is_pingable=0
    )
    node_ids["INTERNET_SERVICE"] = internet_service_id

    # ISP Nodes (attach under INTERNET_SERVICE)
    for isp in ISP_LINKS:
        node_id = insert_node(
            name=isp["name"],
            node_type="ISP",
            ip_address=isp["gateway"],
            parent_id=internet_service_id,
            is_pingable=1
        )
        node_ids[isp["name"]] = node_id

    # Core Server — parent is BSNL_1Gbps (Primary Feed)
    core_id = insert_node(
        name=CORE_SERVER["name"],
        node_type="CORE",
        ip_address=CORE_SERVER["ip"],
        parent_id=node_ids["BSNL_1Gbps"],
        is_pingable=1
    )
    node_ids[CORE_SERVER["name"]] = core_id
    node_ids["CORE"] = core_id

    # VLAN Gateways
    for vlan in VLAN_GATEWAYS:
        # Determine parent ID: either specified by 'parent' name or default to core_id
        parent_name = vlan.get("parent")
        if parent_name:
            actual_parent_id = node_ids.get(parent_name, core_id)
        else:
            actual_parent_id = core_id

        # Use IP from NODE_IPS if available, else from the vlan dict
        node_ip = NODE_IPS.get(vlan["name"], vlan.get("ip"))
        node_pingable = 1 if node_ip else 0

        node_id = insert_node(
            name=vlan["name"],
            node_type="VLAN",
            ip_address=node_ip,
            parent_id=actual_parent_id,
            is_pingable=node_pingable
        )
        node_ids[vlan["name"]] = node_id

    # Logical Blocks — supports multi-level nesting.
    # We iterate until all blocks are resolved (parents may themselves
    # be logical nodes inserted in a previous iteration).
    pending = dict(LOGICAL_BLOCKS)   # shallow copy
    max_passes = 10
    for _ in range(max_passes):
        if not pending:
            break
        still_pending = {}
        for parent_name, children in pending.items():
            parent_id = node_ids.get(parent_name)
            if parent_id is None:
                still_pending[parent_name] = children
                continue
            for child in children:
                # Check if this "logical" child has an IP in NODE_IPS
                child_ip = NODE_IPS.get(child)
                child_pingable = 1 if child_ip else 0
                child_type = "VLAN" if child_ip else "LOGICAL"

                child_id = insert_node(
                    name=child,
                    node_type=child_type,
                    ip_address=child_ip,
                    parent_id=parent_id,
                    is_pingable=child_pingable
                )
                node_ids[child] = child_id
        pending = still_pending

    if pending:
        print(f"WARNING: Could not resolve logical parents: {list(pending.keys())}")

    print("Network nodes populated successfully.")

# ----------------------------------
# Fetch Pingable Nodes
# ----------------------------------

def get_pingable_nodes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, ip_address
        FROM nodes
        WHERE is_pingable = 1 AND is_active = 1
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


# ----------------------------------
# Update Current Status
# ----------------------------------



def update_current_status(node_id, status, latency):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO monitoring_status (node_id, status, latency_ms, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            status=excluded.status,
            latency_ms=excluded.latency_ms,
            last_updated=excluded.last_updated
    """, (node_id, status, latency, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ----------------------------------
# Insert Status History
# ----------------------------------

def insert_status_history(node_id, status, latency):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO status_history (node_id, checked_at, latency_ms, status)
        VALUES (?, ?, ?, ?)
    """, (node_id, datetime.now().isoformat(), latency, status))

    conn.commit()
    conn.close()
# ----------------------------------
# Get Logical Nodes with Parent
# ----------------------------------

def get_logical_nodes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, parent_id
        FROM nodes
        WHERE node_type = 'LOGICAL'
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


# ----------------------------------
# Get Current Status of a Node
# ----------------------------------

def get_current_status(node_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, latency_ms
        FROM monitoring_status
        WHERE node_id = ?
    """, (node_id,))

    row = cursor.fetchone()
    conn.close()
    return row
# ----------------------------------
# Get Previous Status
# ----------------------------------

def get_previous_status(node_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM monitoring_status
        WHERE node_id = ?
    """, (node_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return None
# ----------------------------------
# Insert Alert
# ----------------------------------

def insert_alert(node_id, alert_type, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (node_id, alert_type, alert_time, message)
        VALUES (?, ?, ?, ?)
    """, (node_id, alert_type, datetime.now().isoformat(), message))

    conn.commit()
    conn.close()
def get_node_id_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM nodes WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_node_status_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ms.status
        FROM monitoring_status ms
        JOIN nodes n ON ms.node_id = n.id
        WHERE n.name = ?
    """, (name,))

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_network_links():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source_ip, destination_ip
        FROM network_links
    """)

    rows = cursor.fetchall()

    conn.close()

    links = []

    for row in rows:
        links.append({
            "source": row[0],
            "destination": row[1]
        })

    return links

def get_recent_latencies(node_id, limit=5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT latency_ms
        FROM status_history
        WHERE node_id = ?
        ORDER BY checked_at DESC
        LIMIT ?
    """, (node_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows if row[0] is not None]

def get_node_full_details(node_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            n.id,
            n.name,
            n.node_type,
            n.ip_address,
            ms.status,
            ms.latency_ms,
            ms.last_updated
        FROM nodes n
        LEFT JOIN monitoring_status ms 
        ON n.id = ms.node_id
        WHERE n.id = ?
    """, (node_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

if __name__ == "__main__":
    init_database()
    populate_nodes()

