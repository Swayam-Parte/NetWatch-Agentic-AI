"""Controlled simulated network tools. No live ISP telemetry is accessed."""
from memory.database import connect

NETWORK_STATUS = {
    "Pune": {"outage": False, "severity": "None", "message": "No active network outage reported in the simulated dataset."},
    "Mumbai": {"outage": True, "severity": "Major", "message": "A simulated major network outage is affecting this area."},
    "Nagpur": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
    "Nashik": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
    "Thane": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
    "Navi Mumbai": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
    "Aurangabad": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
    "Kolhapur": {"outage": False, "severity": "None", "message": "No active area outage in the simulated dataset."},
}
WAN_PROBES = {
    "C1001": {"status": "No Link", "message": "Simulated WAN probe reports no link."},
    "C1002": {"status": "No Link", "message": "Simulated WAN probe reports no link."},
    "C1003": {"status": "Unavailable", "message": "Probe unavailable for suspended account."},
    "C1004": {"status": "No Link", "message": "Simulated WAN probe reports no link."},
}


def check_outage(area: str):
    status = NETWORK_STATUS.get(area)
    if not status:
        return {"success": False, "outage": None, "severity": "Unknown", "message": "Area information unavailable."}
    return {"success": True, **status}


def probe_wan(customer_id: str):
    return {"success": customer_id in WAN_PROBES, **WAN_PROBES.get(customer_id, {"status": "Unknown", "message": "No simulated WAN probe result available."})}


def get_recent_event_summary(customer_id: str | None = None, area: str | None = None, limit: int = 50):
    """Return recent synthetic event counts as supplementary evidence."""
    clauses, params = [], []
    if customer_id:
        clauses.append("customer_id=?"); params.append(customer_id)
    if area:
        clauses.append("area=?"); params.append(area)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    try:
        with connect() as conn:
            rows = conn.execute(f"SELECT event_type,severity,metric_value FROM network_events {where} ORDER BY event_time DESC LIMIT ?", (*params, limit)).fetchall()
        counts = {}
        for row in rows:
            counts[row["event_type"]] = counts.get(row["event_type"], 0) + 1
        return {"success": True, "sample_size": len(rows), "event_counts": counts, "source": "synthetic_dataset"}
    except Exception as exc:
        return {"success": False, "sample_size": 0, "event_counts": {}, "message": str(exc), "source": "synthetic_dataset"}


def diagnose_connection(account: dict, outage_info: dict, event_summary: dict | None = None):
    if account.get("account_status") != "Active":
        result = {"diagnosis": "Account issue", "reason": "The customer account is not active."}
    elif outage_info.get("outage") is True:
        result = {"diagnosis": "Area network outage", "reason": outage_info.get("message", "Active outage reported.")}
    elif account.get("router_status") == "Offline":
        result = {"diagnosis": "Router connectivity issue", "reason": "The simulated account snapshot reports the router offline."}
    elif account.get("router_status") == "Online":
        result = {"diagnosis": "Possible WAN, DNS or device connectivity issue", "reason": "Router is online and no area outage is reported; further customer-side checks are required."}
    else:
        result = {"diagnosis": "Unknown connectivity issue", "reason": "Insufficient network evidence."}
    if event_summary and event_summary.get("success"):
        result["recent_event_evidence"] = event_summary
    return result
