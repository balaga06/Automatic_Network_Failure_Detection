# ----------------------------------
# Monitoring Thresholds
# ----------------------------------

PING_COUNT = 3
PING_TIMEOUT = 1          # seconds

HIGH_LATENCY_THRESHOLD = 250   # ms
MONITORING_INTERVAL = 30  # seconds

# ----------------------------------
# Internet (ISP) Configuration
# ----------------------------------

ISP_LINKS = [
    {
        "name": "BSNL_200Mbps",
        "gateway": "117.239.238.66",
        "dns": ["4.2.2.2", "8.8.8.8"]
    },
    {
        "name": "BSNL_1Gbps",
        "gateway": "14.139.85.49",
        "dns": ["4.2.2.2", "8.8.8.8"]
    }
]


# ----------------------------------
# Specific Node IP Mapping
# (Any node listed here will be pinged independently)
# ----------------------------------

NODE_IPS = {
    "MECH": "10.0.56.1",
    "CIVIL": "10.0.55.1",
    "CIVIL LABS": "10.0.51.1",
    "MBA": "10.0.58.1",
    "PHYSICS": "10.0.57.1",
    "NIVIDITHA": "10.0.60.1"
}


# ----------------------------------
# Core Network
# ----------------------------------

CORE_SERVER = {
    "name": "ECE_SERVER_ROOM",
    "ip": "10.0.50.1"
}


# ----------------------------------
# VLAN Gateways (Pingable)
# ----------------------------------

VLAN_GATEWAYS = [
    {"name": "ECE",               "ip": "10.0.52.1"},
    {"name": "CSE",               "ip": "10.0.53.1"},
    {"name": "EEE",               "ip": "10.0.54.1"},
    {"name": "PETROLEUM",         "ip": "10.0.59.1"},
    {"name": "PRINCIPAL_OFFICE",  "ip": "10.0.61.1"},
    {"name": "IRC",               "ip": "10.0.62.1"},
    {"name": "IST",               "ip": "10.0.63.1"},
    {"name": "PHARMACY",          "ip": "10.0.64.1"},
    {"name": "FOOD_TECHNOLOGY",   "ip": "10.0.65.1"},
    {"name": "SWARNOTSAV_BHAVAN", "ip": "10.0.66.1"},
    {"name": "WORKSHOP",          "ip": "10.0.67.1"},
    {"name": "MECH",              "parent": "EEE"},
    {"name": "CIVIL",             "parent": "PRINCIPAL_OFFICE"},
    {"name": "CIVIL LABS",        "parent": "CIVIL"},
    {"name": "MBA",               "parent": "CIVIL"},
    {"name": "PHYSICS",           "parent": "CIVIL"}
]


# ----------------------------------
# Logical / Administrative Hierarchy
# (Non-pingable nodes)
# ----------------------------------

LOGICAL_BLOCKS = {
    # EEE branch
    "EEE": ["LIBRARY", "YOGA_CENTER"],

    # PRINCIPAL_OFFICE branch
    "PRINCIPAL_OFFICE": [
        "HOSTEL_OFFICE",
        "NAGAVALLI 1",
        "NAGAVALLI 2",
        "NIVIDITHA",
        "NALANDA"
    ],

    # HOSTEL_OFFICE
    "HOSTEL_OFFICE": ["CCC_LAB"],

    # CIVIL branch
    "CIVIL": [
        "STAFF QUARTERS A1",
        "STAFF QUARTERS B1"
    ],

    # STAFF QUARTERS B1 sub-branch
    "STAFF QUARTERS B1": ["STAFF QUARTERS B2"]
}


# ----------------------------------
# Currently Known Down VLANs
# ----------------------------------

EXPECTED_DOWN_VLANS = [
    "IRC",
    "IST",
    "PHARMACY",
    "FOOD_TECHNOLOGY",
    "SWARNOTSAV_BHAVAN",
    "WORKSHOP"
]
