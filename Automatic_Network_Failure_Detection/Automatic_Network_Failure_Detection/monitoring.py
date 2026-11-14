from ping3 import ping
from network_config import (
    PING_COUNT,
    PING_TIMEOUT,
    HIGH_LATENCY_THRESHOLD
)
import smtplib
from email.mime.text import MIMEText
import time
from network_config import MONITORING_INTERVAL

from alerts import show_desktop_alert
from database import get_recent_latencies

from database import (
    get_pingable_nodes,
    update_current_status,
    insert_status_history,
    get_logical_nodes,
    get_current_status,
    get_previous_status,
    insert_alert,
    get_node_id_by_name,
    get_node_status_by_name
)
last_status_map = {}
# ----------------------------------
# Ping a Single IP
def ping_host(ip_address):
    latencies = []

    try:
        for _ in range(PING_COUNT):
            response = ping(ip_address, timeout=PING_TIMEOUT)

            # Ignore invalid responses
            if response is not None and response > 0:
                latencies.append(response * 1000)

    except Exception:
        return "DOWN", None

    if not latencies:
        return "DOWN", None

    avg_latency = sum(latencies) / len(latencies)

    if avg_latency > HIGH_LATENCY_THRESHOLD:
        return "HIGH_LATENCY", round(avg_latency, 2)

    return "UP", round(avg_latency, 2)
# ----------------------------------
# Update Logical Node Status
# ----------------------------------

def update_logical_nodes():
    logical_nodes = get_logical_nodes()

    for node_id, name, parent_id in logical_nodes:

        parent_status = get_current_status(parent_id)

        if parent_status:
            status, latency = parent_status

            update_current_status(node_id, status, latency)
            insert_status_history(node_id, status, latency)

            print(f"{name} (Logical) -> {status}")
# ----------------------------------
# Update Aggregated Internet Service
# ----------------------------------

# ----------------------------------
# Update Aggregated Internet Service
# ----------------------------------

def update_internet_service():
    
    # Get status of ISP links and Core
    isp1 = get_node_status_by_name("BSNL_1Gbps")
    isp2 = get_node_status_by_name("BSNL_200Mbps")
    core = get_node_status_by_name("ECE_SERVER_ROOM")

    # Aggregation logic
    if ((isp1 == "UP") or (isp2 == "UP")) and core == "UP":
        service_status = "UP"
    else:
        service_status = "DOWN"

    # Get INTERNET_SERVICE node id
    service_id = get_node_id_by_name("INTERNET_SERVICE")

    previous_status = get_previous_status(service_id)

    update_current_status(service_id, service_status, None)
    insert_status_history(service_id, service_status, None)

    if previous_status is not None and previous_status != service_status:
        change_message = f"INTERNET_SERVICE changed from {previous_status} to {service_status}"

        print(f"⚠ {change_message}")

        insert_alert(service_id, service_status, change_message)
        show_desktop_alert("Internet Service Alert", change_message)

    print(f"INTERNET_SERVICE -> {service_status}")

def send_email_alert(subject, message):

    sender = "yeshoda1807@gmail.com"
    password = "smjwysgssjgblgbb"
    receiver = "yeshoda1807@gmail.com"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)

def predict_failure_trend(node_id):

    latencies = get_recent_latencies(node_id)

    if len(latencies) < 3:
        return "Normal"

    high_latency_count = sum(1 for l in latencies if l > 150)

    if high_latency_count >= 3:
        return "⚠ High Risk: Likely to go DOWN"

    return "Normal"
# ----------------------------------
# Run One Monitoring Cycle
# ----------------------------------
# Add this at TOP of your file (outside function)


def run_monitoring_cycle():
    nodes = get_pingable_nodes()

    print(f"Monitoring {len(nodes)} nodes...\n")

    for node_id, name, ip in nodes:

        current_status_data = get_current_status(node_id)

        if current_status_data:
            previous_status = current_status_data[0]
        else:
            previous_status = None

        status, latency = ping_host(ip)

        # Normalize
        prev = previous_status.strip().upper() if previous_status else None
        curr = status.strip().upper() if status else None

        # Prediction
        prediction = predict_failure_trend(node_id)

        print(f"{name} ({ip}) -> {curr}, {latency} ms")

        # -------------------------------
        # ✅ PREDICTION ALERT (NO DUPLICATE)
        # -------------------------------
        last_pred = last_status_map.get(f"{node_id}_pred")

        if prediction and "High Risk" in prediction and last_pred != "High Risk":

            if curr == "HIGH_LATENCY":

                last_status_map[f"{node_id}_pred"] = "High Risk"

                change_message = f"{name} is under continuous HIGH LATENCY | Prediction: {prediction}"

                print(f"⚠ {change_message}")

                insert_alert(node_id, curr, change_message)

                show_desktop_alert("Prediction Alert", change_message)

                send_email_alert(
                    subject=f"⚠ Warning: {name} may fail soon",
                    message=change_message
                )

        # -------------------------------
        # ✅ STATUS CHANGE ALERT (NO DUPLICATE)
        # -------------------------------
        last_status = last_status_map.get(node_id)

        if prev != curr and last_status != curr:

            last_status_map[node_id] = curr

            if prev is None:
                print(f"{name} initial status set -> {curr}")
            else:
                change_message = f"{name} changed from {prev} to {curr}"

                print(f"⚠ {change_message}")

                insert_alert(node_id, curr, change_message)

                show_desktop_alert("Network Alert", change_message)

                send_email_alert(
                    subject=f"Network Alert: {name}",
                    message=change_message
                )

        # -------------------------------
        # UPDATE DATABASE
        # -------------------------------
        update_current_status(node_id, curr, latency)
        insert_status_history(node_id, curr, latency)

    print("\nUpdating logical nodes...\n")
    update_logical_nodes()

    print("\nUpdating Internet Service...\n")
    update_internet_service()
if __name__ == "__main__":
    print("Starting Continuous Network Monitoring...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            print("====================================")
            print("New Monitoring Cycle")
            print("====================================\n")

            run_monitoring_cycle()

            print(f"\nSleeping for {MONITORING_INTERVAL} seconds...\n")
            time.sleep(MONITORING_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
