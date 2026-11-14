# Automated Network Monitoring and Failure Detection System

## Project Overview

The Automated Network Monitoring and Failure Detection System is a Python-based application designed to monitor network devices and identify connectivity and performance issues in institutional network environments.

The system periodically sends ICMP-based ping requests to configured network nodes, measures response time, and classifies their status as **UP, DOWN, or HIGH LATENCY**.

It stores monitoring information in a centralized SQLite database and displays network status through a Flask-based web dashboard. Email and desktop notifications are generated whenever a network status changes.

## Objectives

- Automate continuous network monitoring.
- Detect network connectivity failures.
- Measure network response time and latency.
- Provide centralized network status visualization.
- Generate alerts when network status changes.
- Maintain historical monitoring and alert records.

## Key Features

### 1. Network Monitoring
- Monitor configured network devices using ICMP ping requests.
- Check device availability periodically.
- Measure network response time and latency.

### 2. Network Status Classification
- **UP:** Network device responds successfully.
- **DOWN:** Network device does not respond.
- **HIGH LATENCY:** Network response time exceeds the configured threshold.

### 3. Network Dashboard
- View network status through a Flask-based dashboard.
- Visualize network topology using map and tree views.
- Add, edit, and delete network nodes.
- View individual device information.

### 4. Alert and Notification System
- Detect network status transitions (UP to DOWN and DOWN to UP).
- Send email notifications using SMTP.
- Generate desktop notifications.
- Maintain alert history with timestamps.

### 5. Database Management
Uses SQLite to maintain:
- Network node details.
- Current network status.
- Historical status records.
- Alert history.

## System Architecture

The application consists of the following components:

1. **Network Devices:** Routers, switches, servers, and other configured network nodes.
2. **Monitoring Engine:** Python and Ping3 perform ICMP-based availability and latency checks.
3. **Database:** SQLite stores network information and monitoring history.
4. **Alert System:** SMTP email and desktop notifications report status changes.
5. **Web Dashboard:** Flask provides the interface for monitoring and managing network devices.
6. **Deployment:** Waitress serves the Flask application, with Ngrok providing optional remote access.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core monitoring logic and backend processing |
| Flask | Web application and dashboard |
| SQLite | Database management |
| Ping3 | Network availability and latency checks |
| ICMP | Network connectivity testing |
| SMTP | Email notifications |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| Waitress | WSGI server |
| Ngrok | Optional remote access |

## Application Workflow

1. Configure network devices using their IP addresses and node names.
2. Send periodic ICMP ping requests to configured devices.
3. Collect responses and measure latency.
4. Classify each device as UP, DOWN, or HIGH LATENCY.
5. Store monitoring information in SQLite.
6. Compare current and previous network status.
7. Generate email and desktop notifications when status changes.
8. Display network information and alert history on the Flask dashboard.

## Project Structure

```text
network-monitoring-system/
│
├── app.py
├── requirements.txt
├── database/
│   └── network.db
│
├── templates/
│   ├── dashboard.html
│   ├── alerts.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── monitoring/
│   ├── network_monitor.py
│   └── ...
│
├── notifications/
│   └── ...
│
└── README.md
```

*Note: Adjust this structure to match the actual files and folders in your repository.*

## Installation and Setup

### Prerequisites

- Python 3.x
- pip
- Git

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Navigate to the Project Directory

```bash
cd network-monitoring-system
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

If a requirements file is not available, install the required packages individually according to your implementation.

### Step 5: Configure Environment Variables

Configure the SMTP email credentials and other required settings using environment variables. Do not commit passwords, API keys, or email credentials to GitHub.

### Step 6: Run the Application

```bash
python app.py
```

Open the local dashboard in your browser using the host and port configured in your
