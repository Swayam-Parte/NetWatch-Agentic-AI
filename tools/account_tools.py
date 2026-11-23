"""Simulated account lookup; reads the generated SQLite dataset first."""
from memory.database import connect

# Original notebook demo identities retained as a safe fallback and regression fixture.
CUSTOMERS = {
 "C1001": {"name":"Rahul Sharma","plan":"Fiber 100 Mbps","account_status":"Active","area":"Pune","router_status":"Online","internet_status":"Disconnected"},
 "C1002": {"name":"Priya Patil","plan":"Fiber 200 Mbps","account_status":"Active","area":"Pune","router_status":"Offline","internet_status":"Disconnected"},
 "C1003": {"name":"Amit Kulkarni","plan":"Fiber 100 Mbps","account_status":"Suspended","area":"Mumbai","router_status":"Online","internet_status":"Disconnected"},
 "C1004": {"name":"Sneha Joshi","plan":"Fiber 500 Mbps","account_status":"Active","area":"Mumbai","router_status":"Online","internet_status":"Disconnected"},
}

def retrieve_account(customer_id: str):
    cid = (customer_id or '').upper()
    account = None
    try:
        with connect() as conn:
            row = conn.execute("SELECT name,plan,account_status,area,router_status,internet_status FROM customers WHERE customer_id=?", (cid,)).fetchone()
        if row:
            account = dict(row)
    except Exception:
        account = None
    if account is None:
        account = CUSTOMERS.get(cid)
    return {"success": bool(account), "account": dict(account) if account else None,
            "message": "Account retrieved from simulated dataset." if account else "Customer ID not found in the simulated knowledge base."}
