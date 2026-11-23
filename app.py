"""NetWatch 2.0 — polished multi-view Streamlit control center (Milestone 4)."""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import settings
from agents.supervisor import SupervisorAgent
from llm.client import GeminiClient
from memory.database import (
    initialize_database, recent_tickets, get_messages, load_conversation,
)
from tools.account_tools import CUSTOMERS
from data.generator import ensure_dataset, dataset_summary
from data.simulation import simulate_event_batch

st.set_page_config(
    page_title="NetWatch | Network Support Control Center",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
DARK_CSS = """
<style>
:root { --nw-bg:#0b1220; --nw-panel:#111c2d; --nw-panel2:#16243a; --nw-border:#263852;
        --nw-text:#e8eef8; --nw-muted:#91a2ba; --nw-cyan:#38bdf8; --nw-green:#34d399; }
.stApp { background:linear-gradient(135deg,#0b1220 0%,#101a2b 55%,#0b1422 100%); color:var(--nw-text); }
[data-testid="stHeader"] { background:rgba(11,18,32,.88); }
.block-container { max-width:1500px; padding-top:1.6rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#0d1727; border-right:1px solid var(--nw-border); }
[data-testid="stMetric"] { background:linear-gradient(145deg,#142238,#101b2d); border:1px solid var(--nw-border);
  padding:16px 18px; border-radius:15px; }
[data-testid="stMetricLabel"] { color:#a8b8cc; }
[data-testid="stMetricValue"] { color:#f2f7ff; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--nw-border); }
.stTabs [data-baseweb="tab"] { background:#111c2d; border:1px solid var(--nw-border); border-radius:10px 10px 0 0; padding:10px 18px; }
.stTabs [aria-selected="true"] { background:#17304b !important; color:#7dd3fc !important; }
div[data-testid="stChatMessage"] { background:#111c2d; border:1px solid #243650; border-radius:14px; padding:12px; }
.nw-hero { background:linear-gradient(115deg,#142943,#102033 60%,#12324a); border:1px solid #2b4967;
  padding:24px 26px; border-radius:18px; margin-bottom:18px; }
.nw-eyebrow { color:#7dd3fc; font-size:12px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; }
.nw-title { font-size:34px; line-height:1.15; font-weight:800; color:#f4f8ff; margin:7px 0; }
.nw-subtitle { color:#a9bbd0; font-size:14px; }
.nw-card { background:linear-gradient(145deg,#142238,#101a2a); border:1px solid var(--nw-border); border-radius:15px; padding:16px; min-height:104px; }
.nw-card-title { color:#a8b8cc; font-size:12px; margin-bottom:9px; }
.nw-card-value { color:#f2f7ff; font-size:24px; font-weight:750; }
.nw-card-note { color:#8da2bc; font-size:12px; margin-top:5px; }
.agent-card { background:#111e30; border:1px solid #293d58; border-radius:12px; padding:13px 14px; margin:7px 0; }
.agent-dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:#34d399; margin-right:9px; box-shadow:0 0 10px #34d39966; }
.small-muted { color:#91a2ba; font-size:12px; }
div.stButton > button { border-radius:10px; }
[data-testid="stDataFrame"] { border:1px solid var(--nw-border); border-radius:12px; overflow:hidden; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

initialize_database()
# Idempotently ensure the initial 1,000-customer synthetic demonstration dataset.
DATASET_COUNTS = ensure_dataset(target_customers=1000, target_events=5000, target_cases=500)
llm = GeminiClient()
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = uuid.uuid4().hex[:12]
if "last_output" not in st.session_state:
    st.session_state.last_output = None

conversation_id = st.session_state.conversation_id
conversation = load_conversation(conversation_id)
messages = get_messages(conversation_id)
tickets = recent_tickets(100)


def read_recent_logs(limit: int = 80):
    db_path = Path(settings.database_path)
    if not db_path.exists():
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT run_id,agent,event,details,created_at FROM execution_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error:
        return []


def metric_card(label: str, value: str, note: str = ""):
    st.markdown(
        f'<div class="nw-card"><div class="nw-card-title">{label}</div>'
        f'<div class="nw-card-value">{value}</div><div class="nw-card-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def status_label(value: str):
    return str(value or "unknown").replace("_", " ").title()


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("# 🌐 NetWatch")
    st.caption("INTELLIGENT CONNECTIVITY SUPPORT")
    st.divider()
    st.markdown("**Platform status**")
    st.write(f"Gemini · `{ 'Connected' if llm.configured else 'Fallback mode' }`")
    st.write(f"Model · `{settings.gemini_model}`")
    st.write("Data source · `Simulated network dataset`")
    st.divider()
    st.markdown("**Active support case**")
    st.code(conversation_id, language=None)
    if st.button("＋  Start new support case", use_container_width=True, type="primary"):
        st.session_state.conversation_id = uuid.uuid4().hex[:12]
        st.session_state.last_output = None
        st.rerun()
    st.caption("Customer and network records are simulated. No live ISP telemetry or external ticketing is connected.")
    st.divider()
    st.markdown("**Demo customer directory**")
    for cid, account in CUSTOMERS.items():
        st.markdown(f"**{cid}** · {account['name']}")
        st.caption(f"{account['area']} · {account['plan']} · Router {account['router_status']}")

# ---------- Hero ----------
st.markdown(
    '<div class="nw-hero"><div class="nw-eyebrow">Agentic AI · Network operations</div>'
    '<div class="nw-title">NetWatch Control Center</div>'
    '<div class="nw-subtitle">A coordinated multi-agent platform for customer intake, network diagnosis, '
    'guided troubleshooting and support escalation.</div></div>',
    unsafe_allow_html=True,
)

# KPI strip
open_tickets = sum(1 for t in tickets if str(t.get("status", "")).upper() == "OPEN")
resolved_count = 1 if conversation and conversation.get("status", "").lower() == "resolved" else 0
k1, k2, k3, k4 = st.columns(4)
with k1: metric_card("PLATFORM VERSION", "2.0 · M5", "Integration, simulation & scale testing")
with k2: metric_card("SPECIALIST AGENTS", "5", "Coordinated by supervisor")
with k3: metric_card("LLM CONNECTIVITY", "Online" if llm.configured else "Fallback", settings.gemini_model)
with k4: metric_card("OPEN SUPPORT TICKETS", str(open_tickets), f"{len(tickets)} recorded locally")

# ---------- Navigation ----------
tab_overview, tab_support, tab_agents, tab_analytics = st.tabs(
    ["⌂  Overview", "✦  Support Console", "◈  Agent Operations", "▥  Tickets & Analytics"]
)

with tab_overview:
    st.subheader("Network operations overview")
    c1, c2 = st.columns([1.35, 1])
    with c1:
        st.markdown("#### Simulated service footprint")
        summary = dataset_summary()
        area_rows = summary["areas"]
        footprint = pd.DataFrame([
            {"Area": row["area"], "Network status": "Major outage (simulated)" if row["area"] == "Mumbai" else "Simulated status", "Customers": row["customers"]}
            for row in area_rows
        ])
        st.dataframe(footprint[["Area", "Network status", "Customers"]], hide_index=True, use_container_width=True)
        fig = px.bar(footprint, x="Area", y="Customers", color="Network status", text="Customers",
                     color_discrete_sequence=["#34d399", "#fb7185"], title="Demo customer distribution by area")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#dce8f6", legend_title_text="", margin=dict(l=10,r=10,t=50,b=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Service health snapshot")
        for area, state, detail in [
            ("Pune", "Operational", "No active area outage in original demo fixture"),
            ("Mumbai", "Major outage", "Simulated area-level service disruption in original demo fixture"),
        ]:
            st.markdown(f'<div class="agent-card"><b>{area}</b><br><span class="small-muted">{detail}</span><br><br>'
                        f'<span class="agent-dot"></span>{state}</div>', unsafe_allow_html=True)
        st.info("Network health indicators are based on the supplied simulated dataset, not live ISP telemetry.")
    st.markdown("#### Recent support activity")
    if tickets:
        st.dataframe(pd.DataFrame(tickets).head(5), hide_index=True, use_container_width=True)
    else:
        st.caption("No tickets have been created yet. Start a support case from the Support Console.")

with tab_support:
    st.subheader("Customer support conversation")
    st.caption(f"Persistent conversation · Case `{conversation_id}`")
    chat_col, context_col = st.columns([1.7, 1])
    with chat_col:
        chat_area = st.container(height=440, border=True)
        with chat_area:
            if not messages:
                st.markdown("### Welcome to NetWatch support")
                st.write("Describe the connectivity issue and include the customer ID. Example:")
                st.info("My internet is not working. Customer ID C1001.")
            else:
                for item in messages:
                    with st.chat_message("user" if item["role"] == "user" else "assistant"):
                        st.markdown(item["content"])
        prompt = st.chat_input("Describe the issue or report what happened after troubleshooting...", key="support_chat_input")
        confirm_clicked = st.button("✓  Confirm that my internet is restored", use_container_width=True)
        if prompt or confirm_clicked:
            user_message = prompt if prompt else "Customer confirms that the internet connection is restored."
            with st.spinner("Supervisor coordinating specialist agents..."):
                try:
                    output = SupervisorAgent(llm=llm).run(
                        user_message,
                        customer_confirmed_resolved=confirm_clicked,
                        conversation_id=conversation_id,
                    )
                    st.session_state.last_output = output
                    st.rerun()
                except Exception as exc:
                    st.error(f"Workflow error: {exc}")
    with context_col:
        st.markdown("#### Case context")
        state = conversation.get("state", {}) if conversation else {}
        customer = state.get("customer") or {}
        st.metric("Customer", customer.get("name", "Not identified"))
        st.metric("Area", customer.get("area", "—"))
        st.metric("Case status", status_label(conversation.get("status")) if conversation else "New")
        st.metric("Troubleshooting attempts", conversation.get("attempts", 0) if conversation else 0)
        st.caption("Customer confirmation is required before a case is marked resolved.")

    # Render persisted assessment even after page refresh.
    output = st.session_state.get("last_output")
    result = output.get("result") if output and output.get("conversation_id") == conversation_id else None
    state = (load_conversation(conversation_id) or {}).get("state", {})
    if result or state.get("diagnosis"):
        st.divider()
        st.markdown("#### Latest case assessment")
        result = result or {}
        diagnosis = (result.get("diagnosis") or {}).get("tool_diagnosis", {})
        if not diagnosis and state.get("diagnosis"):
            diagnosis = {"diagnosis": state.get("diagnosis"), "reason": "Diagnosis retained in persistent case memory."}
        status = result.get("status") or (load_conversation(conversation_id) or {}).get("status", "pending_customer")
        st.info(f"Status: {status_label(status)} · Attempts: {state.get('attempts', 0)}")
        if diagnosis:
            st.markdown(f"**Diagnosis:** {diagnosis.get('diagnosis', '—')}  \n{diagnosis.get('reason', '')}")
        recommendations = (result.get("troubleshooting") or {}).get("steps") or state.get("last_recommendations", [])
        if recommendations:
            st.markdown("**Recommended actions**")
            for step in recommendations:
                st.markdown(f"- {step}")
        if output and output.get("events"):
            with st.expander("View latest agent execution trace"):
                for event in output["events"]:
                    st.write(f"**{event['agent']} · {event['event']}**", event["details"])

with tab_agents:
    st.subheader("Agent operations center")
    st.caption("Independent specialist modules coordinated by the Supervisor Agent.")
    agent_info = [
        ("Supervisor Agent", "Workflow planning, shared state, retries and orchestration", "agents/supervisor.py"),
        ("Customer Agent", "Intent extraction and simulated account retrieval", "agents/customer_agent.py"),
        ("Network Diagnosis Agent", "Outage checks, router evidence and WAN diagnosis", "agents/diagnosis_agent.py"),
        ("Memory Agent", "Historical case retrieval and conversation context", "agents/memory_agent.py"),
        ("Troubleshooting Agent", "Context-aware recommendations and next steps", "agents/troubleshooting_agent.py"),
        ("Verification & Escalation Agent", "Resolution checks and local support ticket creation", "agents/verification_agent.py"),
    ]
    logs = read_recent_logs(100)
    latest_by_agent = {}
    for log in logs:
        latest_by_agent.setdefault(log["agent"], log)
    cols = st.columns(2)
    for index, (name, purpose, module) in enumerate(agent_info):
        with cols[index % 2]:
            latest = latest_by_agent.get(name)
            last_event = latest["event"] if latest else "Waiting for workflow"
            st.markdown(
                f'<div class="agent-card"><span class="agent-dot"></span><b>{name}</b><br>'
                f'<span class="small-muted">{purpose}</span><br><br>'
                f'<span class="small-muted">Module: {module}<br>Last event: {last_event}</span></div>',
                unsafe_allow_html=True,
            )
    st.markdown("#### Execution event stream")
    if logs:
        log_df = pd.DataFrame(logs)
        st.dataframe(log_df[["created_at", "run_id", "agent", "event", "details"]].head(30),
                     hide_index=True, use_container_width=True)
    else:
        st.caption("No agent executions recorded yet. Start a support conversation to populate this view.")

with tab_analytics:
    st.subheader("Support tickets & analytics")
    st.markdown("#### Synthetic dataset operations")
    st.caption("All records are fictional. The generator is deterministic for initial seeding and append-only for runtime events.")
    current_summary = dataset_summary()
    ds = current_summary["counts"]
    d1, d2, d3, d4 = st.columns(4)
    with d1: st.metric("Customers", f"{ds['customers']:,}")
    with d2: st.metric("Network devices", f"{ds['devices']:,}")
    with d3: st.metric("Network events", f"{ds['events']:,}")
    with d4: st.metric("Historical cases", f"{ds['historical_cases']:,}")
    event_col, area_col = st.columns([1, 1])
    with event_col:
        event_batch = st.selectbox("Runtime event batch", [25, 100, 250, 500], index=1, key="event_batch_size")
        if st.button("Generate simulated network events", key="generate_events", use_container_width=True):
            generated = simulate_event_batch(int(event_batch))
            st.success(generated["message"])
            st.rerun()
    with area_col:
        area_df = pd.DataFrame(current_summary["areas"])
        if not area_df.empty:
            area_df.columns = ["Area", "Customers"]
            st.markdown("**Customer distribution by area**")
            st.dataframe(area_df, hide_index=True, use_container_width=True)
    event_df = pd.DataFrame(current_summary["event_types"])
    if not event_df.empty:
        event_df.columns = ["Event type", "Events"]
        st.markdown("**Synthetic network event distribution**")
        st.dataframe(event_df, hide_index=True, use_container_width=True)
    st.info("The four original jury demo accounts (C1001–C1004) are preserved. Generated accounts use IDs C1005 onward. Runtime events append to the database and do not overwrite previous events.")
    st.divider()
    if tickets:
        ticket_df = pd.DataFrame(tickets)
        x, y, z = st.columns(3)
        with x: st.metric("Total tickets", len(ticket_df))
        with y: st.metric("Open tickets", int((ticket_df["status"].str.upper() == "OPEN").sum()))
        with z: st.metric("Unique customers", ticket_df["customer_id"].nunique())
        status_counts = ticket_df["status"].fillna("UNKNOWN").str.upper().value_counts().rename_axis("Status").reset_index(name="Tickets")
        fig = px.pie(status_counts, names="Status", values="Tickets", hole=.55, title="Ticket status distribution",
                     color_discrete_sequence=["#38bdf8", "#34d399", "#fb7185", "#a78bfa"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#dce8f6", height=330,
                          legend_title_text="", margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### Ticket register")
        st.dataframe(ticket_df, hide_index=True, use_container_width=True)
    else:
        st.metric("Total tickets", 0)
        st.info("No support tickets have been generated yet. Trigger an outage or account-restriction scenario (for example C1004 or C1003) in the Support Console to demonstrate escalation.")

st.divider()
st.markdown(
    '<div class="small-muted">NETWATCH 2.0 · Academic prototype · Simulated customer/network records · '
    'Gemini-powered language reasoning with deterministic support tools</div>',
    unsafe_allow_html=True,
)
