import sys
import os
import webbrowser
import threading




# FIX for EXE and normal run
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = os.path.join(BASE_DIR, "network_monitor.db")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_recent_latencies

from flask import Flask, render_template
from database import get_network_links



import sqlite3
from flask import request, redirect, url_for

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "dashboard", "templates"),
    static_folder=os.path.join(BASE_DIR, "dashboard", "static")
)

app.config["DEBUG"] = True


    


def get_connection():
      # 👈 ADD THIS
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def predict_failure_trend_ui(latencies):

    if len(latencies) < 3:
        return "Normal"

    high_latency_count = sum(1 for l in latencies if l > 150)

    if high_latency_count >= 3:
        return "⚠ High Risk: Likely to go DOWN"

    return "Normal"

@app.route("/")
def dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch nodes
    cursor.execute("""
        SELECT n.id, n.name, n.node_type, n.parent_id,
               ms.status, ms.latency_ms, ms.last_updated
        FROM nodes n
        LEFT JOIN monitoring_status ms ON n.id = ms.node_id
    """)
    rows = cursor.fetchall()

    # Fetch latest 5 alerts
    cursor.execute("""
        SELECT a.id, n.name, a.alert_type, a.alert_time, a.message
        FROM alerts a
        JOIN nodes n ON a.node_id = n.id
        ORDER BY a.alert_time DESC
        LIMIT 5
    """)
    recent_alerts = cursor.fetchall()

    conn.close()

    # Build tree
    nodes = {}
    for row in rows:
        nodes[row["id"]] = dict(row)
        nodes[row["id"]]["children"] = []

    root_nodes = []
    for node_id, node in nodes.items():
        parent_id = node["parent_id"]
        if parent_id:
            nodes[parent_id]["children"].append(node)
        else:
            root_nodes.append(node)

    return render_template(
        "dashboard.html",
        roots=root_nodes,
        recent_alerts=recent_alerts
    )

@app.route("/node/<int:node_id>")
def node_detail(node_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT n.name, n.node_type,
               ms.status, ms.latency_ms, ms.last_updated
        FROM nodes n
        LEFT JOIN monitoring_status ms ON n.id = ms.node_id
        WHERE n.id = ?
    """, (node_id,))

    node = cursor.fetchone()
    conn.close()

    # ✅ ADD THIS
    latencies = get_recent_latencies(node_id)
    prediction = predict_failure_trend_ui(latencies)

    return render_template(
        "node_detail.html",
        node=node,
        prediction=prediction   # ✅ PASS TO HTML
    )
from flask import jsonify

@app.route("/api/node/<int:node_id>")
def get_node_details(node_id):
    from database import get_node_full_details
    from monitoring import predict_failure_trend  # if separate file

    node = get_node_full_details(node_id)

    if not node:
        return jsonify({"error": "Node not found"}), 404

    prediction = predict_failure_trend(node_id)

    return jsonify({
        "id": node["id"],
        "name": node["name"],
        "node_type": node["node_type"],
        "ip_address": node.get("ip_address"),   # ✅ NEW
        "status": node.get("status"),
        "latency_ms": node.get("latency_ms"),
        "last_updated": node.get("last_updated"),
        "prediction": prediction
    })
@app.route("/alerts")
def alerts_page():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, n.name, a.alert_type, a.alert_time, a.message
        FROM alerts a
        JOIN nodes n ON a.node_id = n.id
        ORDER BY a.alert_time DESC
    """)

    alerts = cursor.fetchall()
    conn.close()

    return render_template("alerts.html", alerts=alerts)
@app.route("/add_vlan")
def add_vlan_form():

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch possible parent nodes
    cursor.execute("""
    SELECT id, name
    FROM nodes
    WHERE is_active = 1
    AND node_type IN ('CORE', 'VLAN', 'LOGICAL')   -- ✅ FIX
    ORDER BY name
""")

    parents = cursor.fetchall()
    conn.close()

    return render_template("add_vlan.html", parents=parents)
@app.route("/add_vlan", methods=["POST"])
def add_vlan():

    name = request.form["name"]
    ip = request.form["ip"]
    parent_id = request.form["parent_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nodes (name, node_type, ip_address, parent_id, is_pingable)
        VALUES (?, 'VLAN', ?, ?, 1)
    """, (name, ip, parent_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))
@app.route("/edit_node/<int:node_id>")
def edit_node(node_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM nodes WHERE id = ?
    """, (node_id,))
    node = cursor.fetchone()

    cursor.execute("""
    SELECT id, name FROM nodes
    WHERE is_active = 1
    AND node_type IN ('CORE','VLAN','LOGICAL')   -- ✅ FIX
    ORDER BY name
""")
    parents = cursor.fetchall()

    conn.close()

    return render_template("edit_node.html", node=node, parents=parents)
@app.route("/update_node/<int:node_id>", methods=["POST"])
def update_node(node_id):

    name = request.form["name"]
    ip = request.form["ip"]
    parent_id = request.form["parent_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE nodes
        SET name=?, ip_address=?, parent_id=?
        WHERE id=?
    """, (name, ip, parent_id, node_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))
@app.route("/delete_node/<int:node_id>")
def delete_node(node_id):

    conn = get_connection()
    cursor = conn.cursor()

    # Check if node has children
    cursor.execute(
        "SELECT COUNT(*) FROM nodes WHERE parent_id = ?", (node_id,)
    )
    child_count = cursor.fetchone()[0]

    if child_count > 0:
        conn.close()
        return "Cannot delete node. It has child nodes."

    # Delete monitoring data first
    cursor.execute("DELETE FROM monitoring_status WHERE node_id=?", (node_id,))
    cursor.execute("DELETE FROM status_history WHERE node_id=?", (node_id,))
    cursor.execute("DELETE FROM alerts WHERE node_id=?", (node_id,))

    # Delete node
    cursor.execute("DELETE FROM nodes WHERE id=?", (node_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))



@app.route("/topology")
def topology():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT n.id,
               n.name,
               n.node_type,
               n.parent_id,
               n.ip_address,
               ms.status,
               ms.latency_ms
        FROM nodes n
        LEFT JOIN monitoring_status ms
        ON n.id = ms.node_id
    """)

    rows = cursor.fetchall()
    conn.close()

    # Build recursive tree (same approach as dashboard)
    node_map = {}
    for row in rows:
        node_map[row["id"]] = {
            "id":         row["id"],
            "name":       row["name"],
            "node_type":  row["node_type"],
            "parent_id":  row["parent_id"],
            "ip_address": row["ip_address"],
            "status":     row["status"],
            "latency_ms": row["latency_ms"],
            "children":   []
        }

    roots = []
    for node in node_map.values():
        pid = node["parent_id"]
        if pid and pid in node_map:
            node_map[pid]["children"].append(node)
        else:
            roots.append(node)

    return render_template("topology.html", roots=roots)


if __name__ == "__main__":

    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)