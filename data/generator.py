"""Reproducible, idempotent synthetic dataset generator for NetWatch.

All records are fictional and intended for academic demonstrations only.
"""
from __future__ import annotations
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from memory.database import connect, initialize_database

TARGET_CUSTOMERS = 1000
TARGET_EVENTS = 5000
TARGET_HISTORICAL_CASES = 500
AREAS = ["Pune", "Mumbai", "Nagpur", "Nashik", "Thane", "Navi Mumbai", "Aurangabad", "Kolhapur"]
PLANS = ["Fiber 50 Mbps", "Fiber 100 Mbps", "Fiber 200 Mbps", "Fiber 500 Mbps", "Fiber 1 Gbps"]
FIRST_NAMES = ["Aarav", "Aditi", "Aditya", "Ananya", "Arjun", "Diya", "Isha", "Kabir", "Kavya", "Meera", "Neha", "Rohan", "Saanvi", "Vihaan", "Ishaan", "Tanvi", "Reyansh", "Mira", "Dev", "Anika"]
LAST_NAMES = ["Sharma", "Patil", "Kulkarni", "Joshi", "Deshmukh", "Shah", "More", "Pawar", "Gupta", "Naik", "Jadhav", "Kadam", "Chavan", "Mehta", "Rao"]

# Original notebook/demo identities are preserved exactly.
BASE_CUSTOMERS = {
    "C1001": {"name":"Rahul Sharma", "plan":"Fiber 100 Mbps", "account_status":"Active", "area":"Pune", "router_status":"Online", "internet_status":"Disconnected"},
    "C1002": {"name":"Priya Patil", "plan":"Fiber 200 Mbps", "account_status":"Active", "area":"Pune", "router_status":"Offline", "internet_status":"Disconnected"},
    "C1003": {"name":"Amit Kulkarni", "plan":"Fiber 100 Mbps", "account_status":"Suspended", "area":"Mumbai", "router_status":"Online", "internet_status":"Disconnected"},
    "C1004": {"name":"Sneha Joshi", "plan":"Fiber 500 Mbps", "account_status":"Active", "area":"Mumbai", "router_status":"Online", "internet_status":"Disconnected"},
}
EVENT_TYPES = ["latency_spike", "packet_loss", "wan_disconnect", "router_reboot", "dns_failure", "link_restored"]


def _customer_record(customer_id: str, rng: random.Random) -> dict:
    if customer_id in BASE_CUSTOMERS:
        return dict(BASE_CUSTOMERS[customer_id])
    area = rng.choice(AREAS)
    account_status = "Suspended" if rng.random() < 0.035 else "Active"
    router_status = "Offline" if rng.random() < 0.09 else "Online"
    internet_status = "Connected" if router_status == "Online" and account_status == "Active" and rng.random() > 0.06 else "Disconnected"
    return {"name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}", "plan": rng.choice(PLANS),
            "account_status": account_status, "area": area, "router_status": router_status,
            "internet_status": internet_status}


def ensure_schema():
    initialize_database()
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY, name TEXT NOT NULL, plan TEXT NOT NULL,
            account_status TEXT NOT NULL, area TEXT NOT NULL, router_status TEXT NOT NULL,
            internet_status TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS network_devices (
            device_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL UNIQUE, area TEXT NOT NULL,
            device_type TEXT NOT NULL, firmware_version TEXT NOT NULL, last_seen TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS network_events (
            event_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, device_id TEXT NOT NULL,
            area TEXT NOT NULL, event_type TEXT NOT NULL, severity TEXT NOT NULL,
            metric_value REAL, event_time TEXT NOT NULL, source TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS historical_cases (
            case_id TEXT PRIMARY KEY, customer_id TEXT, area TEXT NOT NULL, problem TEXT NOT NULL,
            resolution TEXT NOT NULL, outcome TEXT NOT NULL, created_at TEXT NOT NULL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_area ON customers(area)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_customer_time ON network_events(customer_id,event_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_area ON network_events(area)")


def generate_network_events(count: int = 100, seed: int | None = None) -> int:
    """Append a deterministic-sized batch of new synthetic events; never deletes existing rows."""
    if count < 1 or count > 100000:
        raise ValueError("count must be between 1 and 100000")
    ensure_schema()
    rng = random.Random(seed)
    with connect() as conn:
        customers = [dict(r) for r in conn.execute("SELECT customer_id,area FROM customers").fetchall()]
        devices = {r["customer_id"]: r["device_id"] for r in conn.execute("SELECT customer_id,device_id FROM network_devices").fetchall()}
        if not customers:
            raise RuntimeError("Generate the customer dataset before generating events.")
        now = datetime.now(timezone.utc)
        rows = []
        for i in range(count):
            customer = rng.choice(customers)
            event_type = rng.choice(EVENT_TYPES)
            if event_type == "latency_spike": value = round(rng.uniform(150, 900), 2)
            elif event_type == "packet_loss": value = round(rng.uniform(2, 35), 2)
            else: value = None
            severity = "critical" if event_type == "wan_disconnect" else ("high" if event_type in {"packet_loss", "dns_failure"} else "medium")
            rows.append((uuid.uuid4().hex, customer["customer_id"], devices[customer["customer_id"]], customer["area"],
                         event_type, severity, value, (now - timedelta(seconds=i * 17)).isoformat(), "synthetic_runtime"))
        conn.executemany("""INSERT INTO network_events(event_id,customer_id,device_id,area,event_type,severity,metric_value,event_time,source)
            VALUES(?,?,?,?,?,?,?,?,?)""", rows)
    return len(rows)


def ensure_dataset(target_customers: int = TARGET_CUSTOMERS, target_events: int = TARGET_EVENTS,
                   target_cases: int = TARGET_HISTORICAL_CASES, seed: int = 20261123) -> dict:
    """Ensure minimum target row counts. Existing rows and original IDs are retained."""
    if not (4 <= target_customers <= 100000):
        raise ValueError("target_customers must be between 4 and 100000")
    if not (0 <= target_events <= 1000000 and 0 <= target_cases <= 100000):
        raise ValueError("event/case target is outside the supported range")
    ensure_schema()
    rng = random.Random(seed)
    with connect() as conn:
        # Seed the original four records before allocating generated IDs.
        for cid, record in BASE_CUSTOMERS.items():
            conn.execute("INSERT OR IGNORE INTO customers(customer_id,name,plan,account_status,area,router_status,internet_status) VALUES(?,?,?,?,?,?,?)",
                         (cid, record["name"], record["plan"], record["account_status"], record["area"], record["router_status"], record["internet_status"]))
        existing_ids = {r[0] for r in conn.execute("SELECT customer_id FROM customers")}
        customers_to_add = []
        devices_to_add = []
        next_num = 1001
        reserved_ids = set(existing_ids)
        while len(existing_ids) + len(customers_to_add) < target_customers:
            cid = f"C{next_num}"
            next_num += 1
            if cid in reserved_ids: continue
            record = _customer_record(cid, rng)
            customers_to_add.append((cid, record["name"], record["plan"], record["account_status"], record["area"], record["router_status"], record["internet_status"]))
            reserved_ids.add(cid)
        for cid, name, plan, account_status, area, router_status, internet_status in customers_to_add:
            devices_to_add.append((f"R-{cid}", cid, area, "Fiber Router", f"{rng.randint(1,4)}.{rng.randint(0,9)}.{rng.randint(0,9)}", datetime.now(timezone.utc).isoformat()))
        # Ensure the original four and any existing imported records have device rows too.
        existing_devices = {r[0] for r in conn.execute("SELECT customer_id FROM network_devices")}
        for cid, record in BASE_CUSTOMERS.items():
            if cid not in {r[0] for r in conn.execute("SELECT customer_id FROM customers")}:
                conn.execute("INSERT INTO customers(customer_id,name,plan,account_status,area,router_status,internet_status) VALUES(?,?,?,?,?,?,?)",
                             (cid, record["name"], record["plan"], record["account_status"], record["area"], record["router_status"], record["internet_status"]))
            if cid not in existing_devices:
                devices_to_add.append((f"R-{cid}", cid, record["area"], "Fiber Router", "2.1.0", datetime.now(timezone.utc).isoformat()))
        conn.executemany("INSERT OR IGNORE INTO customers(customer_id,name,plan,account_status,area,router_status,internet_status) VALUES(?,?,?,?,?,?,?)", customers_to_add)
        conn.executemany("INSERT OR IGNORE INTO network_devices(device_id,customer_id,area,device_type,firmware_version,last_seen) VALUES(?,?,?,?,?,?)", devices_to_add)
        current_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        current_events = conn.execute("SELECT COUNT(*) FROM network_events").fetchone()[0]
        current_cases = conn.execute("SELECT COUNT(*) FROM historical_cases").fetchone()[0]
        # Initial event population is generated in-place for speed and reproducibility.
        if current_events < target_events:
            customer_rows = [dict(r) for r in conn.execute("SELECT customer_id,area FROM customers").fetchall()]
            device_map = {r["customer_id"]: r["device_id"] for r in conn.execute("SELECT customer_id,device_id FROM network_devices").fetchall()}
            batch = []
            # Fixed seed timestamp keeps the initial demonstration extract reproducible.
            now = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
            for i in range(target_events - current_events):
                c = customer_rows[rng.randrange(len(customer_rows))]
                kind = EVENT_TYPES[rng.randrange(len(EVENT_TYPES))]
                value = round(rng.uniform(150, 900), 2) if kind == "latency_spike" else (round(rng.uniform(2, 35), 2) if kind == "packet_loss" else None)
                severity = "critical" if kind == "wan_disconnect" else ("high" if kind in {"packet_loss", "dns_failure"} else "medium")
                batch.append((f"SEED-EVT-{current_events+i+1:07d}", c["customer_id"], device_map[c["customer_id"]], c["area"], kind, severity, value,
                              (now - timedelta(minutes=i)).isoformat(), "synthetic_seed"))
            conn.executemany("INSERT INTO network_events(event_id,customer_id,device_id,area,event_type,severity,metric_value,event_time,source) VALUES(?,?,?,?,?,?,?,?,?)", batch)
        if current_cases < target_cases:
            cases = []
            templates = [
                ("Router offline and internet unavailable", "Verify power, inspect cables and restart router safely."),
                ("High latency during peak hours", "Check congestion indicators and compare latency across time windows."),
                ("Packet loss on fiber connection", "Inspect WAN link quality and escalate persistent packet loss."),
                ("WAN link disconnected", "Check physical WAN connection and request service-side verification."),
                ("DNS resolution failure", "Verify DNS configuration and test with an approved alternate resolver."),
                ("Area outage reported", "Communicate outage status and route case to network operations."),
            ]
            customers = [r[0] for r in conn.execute("SELECT customer_id FROM customers").fetchall()]
            now = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
            for i in range(target_cases - current_cases):
                problem, resolution = templates[i % len(templates)]
                cases.append((f"HCASE-{current_cases+i+1:06d}", rng.choice(customers), rng.choice(AREAS), problem, resolution,
                              rng.choice(["resolved", "escalated", "monitoring"]), (now - timedelta(days=i % 365)).isoformat()))
            conn.executemany("INSERT OR IGNORE INTO historical_cases(case_id,customer_id,area,problem,resolution,outcome,created_at) VALUES(?,?,?,?,?,?,?)", cases)
        # Keep original four rows exact even if database already existed from a previous run.
        for cid, record in BASE_CUSTOMERS.items():
            conn.execute("UPDATE customers SET name=?,plan=?,account_status=?,area=?,router_status=?,internet_status=? WHERE customer_id=?",
                         (record["name"],record["plan"],record["account_status"],record["area"],record["router_status"],record["internet_status"],cid))
        counts = {
            "customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            "devices": conn.execute("SELECT COUNT(*) FROM network_devices").fetchone()[0],
            "events": conn.execute("SELECT COUNT(*) FROM network_events").fetchone()[0],
            "historical_cases": conn.execute("SELECT COUNT(*) FROM historical_cases").fetchone()[0],
        }
    return counts


def dataset_summary() -> dict:
    ensure_schema()
    with connect() as conn:
        counts = {
            "customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            "devices": conn.execute("SELECT COUNT(*) FROM network_devices").fetchone()[0],
            "events": conn.execute("SELECT COUNT(*) FROM network_events").fetchone()[0],
            "historical_cases": conn.execute("SELECT COUNT(*) FROM historical_cases").fetchone()[0],
        }
        areas = [dict(r) for r in conn.execute("SELECT area, COUNT(*) AS customers FROM customers GROUP BY area ORDER BY customers DESC")]
        event_types = [dict(r) for r in conn.execute("SELECT event_type, COUNT(*) AS events FROM network_events GROUP BY event_type ORDER BY events DESC")]
        return {"counts": counts, "areas": areas, "event_types": event_types}
