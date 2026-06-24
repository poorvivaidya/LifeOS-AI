import streamlit as st
import sqlite3
import os
import json
import base64
import urllib.request
import time

# Set page configuration with a modern dark theme layout
st.set_page_config(
    page_title="LifeOS AI – Multi-Agent Personal Life OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling for Outfit font, HSL color harmonies, glow borders, and transition effects
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0b0f19 !important;
        color: #f1f5f9 !important;
    }
    
    /* Main title custom gradient styling */
    .main-header {
        font-size: 46px;
        font-weight: 800;
        background: linear-gradient(135deg, #a5b4fc, #ec4899, #f43f5e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        letter-spacing: -1.5px;
    }
    
    .subtitle {
        font-size: 16px;
        color: #94a3b8;
        margin-bottom: 30px;
    }
    
    /* Style Streamlit's native bordered containers to look premium, glassmorphic and animated */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6)) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 15px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(129, 140, 248, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(129, 140, 248, 0.12) !important;
    }
    
    /* Style Streamlit forms similarly */
    div[data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6)) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stForm"]:hover {
        border-color: rgba(129, 140, 248, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(129, 140, 248, 0.12) !important;
    }
    
    /* Sidebar custom styling */
    [data-testid="stSidebar"] {
        background-color: #070a13 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Custom container card with glow on hover */
    .premium-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6));
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3);
    }
    .premium-card:hover {
        border-color: rgba(129, 140, 248, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(129, 140, 248, 0.12);
    }
    
    /* Grid Stat Cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.7));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stat-card:hover {
        transform: translateY(-2px);
        border-color: rgba(129, 140, 248, 0.3);
        box-shadow: 0 8px 25px rgba(129, 140, 248, 0.12);
    }
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
    }
    .stat-card-goals::before { background: linear-gradient(to bottom, #818cf8, #4f46e5); }
    .stat-card-schedule::before { background: linear-gradient(to bottom, #38bdf8, #0284c7); }
    .stat-card-habits::before { background: linear-gradient(to bottom, #f472b6, #db2777); }
    .stat-card-learning::before { background: linear-gradient(to bottom, #34d399, #059669); }
    
    .stat-val {
        font-size: 34px;
        font-weight: 800;
        margin-top: 10px;
        background: linear-gradient(135deg, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        font-size: 11px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Section headers */
    .section-title {
        font-size: 24px;
        font-weight: 700;
        margin-top: 35px;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
        color: #f1f5f9;
        letter-spacing: -0.5px;
    }
    
    /* Timelines */
    .timeline-item {
        border-left: 2px dashed rgba(129, 140, 248, 0.4);
        padding-left: 20px;
        margin-left: 10px;
        padding-bottom: 20px;
        position: relative;
    }
    .timeline-item:last-child {
        border-left: none;
    }
    .timeline-item::before {
        content: '';
        width: 12px;
        height: 12px;
        background: linear-gradient(135deg, #a5b4fc, #db2777);
        border-radius: 50%;
        position: absolute;
        left: -7px;
        top: 6px;
        box-shadow: 0 0 10px rgba(165, 180, 252, 0.6);
    }
    
    /* Colorful Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 8px;
        letter-spacing: 0.5px;
    }
    .badge-high { background-color: rgba(239, 68, 68, 0.12); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.25); }
    .badge-med { background-color: rgba(245, 158, 11, 0.12); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.25); }
    .badge-low { background-color: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.25); }
    
    /* Primary buttons */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #818cf8, #db2777) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(219, 39, 119, 0.3) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #a5b4fc, #ec4899) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(219, 39, 119, 0.5) !important;
    }
    
    /* Secondary buttons */
    button[data-testid="baseButton-secondary"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        border-color: rgba(129, 140, 248, 0.3) !important;
        background: rgba(30, 41, 59, 0.7) !important;
        color: white !important;
    }
    
    /* Inputs styling override */
    div[data-testid="stTextArea"] textarea, 
    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stTextArea"] textarea:focus, 
    div[data-testid="stTextInput"] input:focus, 
    div[data-testid="stNumberInput"] input:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 10px rgba(129, 140, 248, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Database helper functions
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lifeos.db")
BACKEND_URL = "http://localhost:8080"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_all(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []

# ADK Backend Session client
def trigger_goal_workflow(goal_text, duration_days, submitter, category, date_target):
    url = f"{BACKEND_URL}/apps/expense_agent/trigger/pubsub"
    payload_data = {
        "amount": float(duration_days),
        "submitter": submitter,
        "category": category,
        "description": goal_text,
        "date": date_target
    }
    encoded = base64.b64encode(json.dumps(payload_data).encode()).decode()
    body = {
        "message": {
            "data": encoded,
            "attributes": {"source": "streamlit"}
        },
        "subscription": "test-sub"
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(body).encode(), 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def fetch_pending_sessions():
    import concurrent.futures
    url = f"{BACKEND_URL}/apps/expense_agent/users/test-sub/sessions"
    try:
        if "session_cache" not in st.session_state:
            st.session_state.session_cache = {}
            
        with urllib.request.urlopen(url) as resp:
            sessions = json.loads(resp.read().decode())
        
        cache = st.session_state.session_cache
        
        # Prune cache to avoid leaks
        current_keys = {(s["id"], s.get("lastUpdateTime", 0)) for s in sessions}
        for k in list(cache.keys()):
            if k not in current_keys:
                cache.pop(k, None)
                
        sessions_to_fetch = []
        for s in sessions:
            cache_key = (s["id"], s.get("lastUpdateTime", 0))
            if cache_key not in cache:
                sessions_to_fetch.append(s)
                
        def fetch_one(s):
            s_url = f"{BACKEND_URL}/apps/expense_agent/users/test-sub/sessions/{s['id']}"
            try:
                with urllib.request.urlopen(s_url) as s_resp:
                    full_session = json.loads(s_resp.read().decode())
                
                calls = {}
                responses = set()
                review_summary = None
                
                for event in full_session.get("events", []):
                    content = event.get("content") or {}
                    parts = content.get("parts") or []
                    for part in parts:
                        fc = part.get("functionCall")
                        if fc:
                            name = fc.get("name")
                            if name == "emit_expense_alert":
                                review_summary = fc.get("args", {}).get("risk_summary")
                            elif name == "adk_request_input":
                                args = fc.get("args", {})
                                payload = args.get("payload") or {}
                                if isinstance(payload, str):
                                    try:
                                        payload = json.loads(payload)
                                    except Exception:
                                        pass
                                calls[fc["id"]] = {
                                    "session_id": full_session["id"],
                                    "interrupt_id": fc["id"],
                                    "message": args.get("message", ""),
                                    "payload": payload,
                                    "user_id": full_session["userId"]
                                }
                        fr = part.get("functionResponse")
                        if fr and fr.get("name") == "adk_request_input":
                            responses.add(fr["id"])
                
                pending_calls = []
                for cid, call_info in calls.items():
                    if cid not in responses:
                        if review_summary:
                            call_info["review"] = review_summary
                        pending_calls.append(call_info)
                return s["id"], s.get("lastUpdateTime", 0), pending_calls
            except Exception:
                return s["id"], s.get("lastUpdateTime", 0), []

        if sessions_to_fetch:
            with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
                results = list(executor.map(fetch_one, sessions_to_fetch))
            for sid, lut, pending_calls in results:
                cache[(sid, lut)] = pending_calls
                
        pending_list = []
        for s in sessions:
            cache_key = (s["id"], s.get("lastUpdateTime", 0))
            cached_pending = cache.get(cache_key)
            if cached_pending:
                pending_list.extend(cached_pending)
        return pending_list
    except Exception as e:
        return []

def resume_session(session_id, interrupt_id, approved):
    url = f"{BACKEND_URL}/run"
    data = {
      "appName": "expense_agent",
      "userId": "test-sub",
      "sessionId": session_id,
      "newMessage": {
        "role": "user",
        "parts": [
          {
            "functionResponse": {
              "id": interrupt_id,
              "name": "adk_request_input",
              "response": {
                "result": json.dumps({"decision": "approve" if approved else "reject"})
              }
            }
          }
        ]
      }
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode(), 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown("""
<div style='text-align: center; padding: 15px;'>
    <span style='font-size: 40px;'>🧠</span>
    <h2 style='margin: 10px 0 0 0; font-weight: 800; background: linear-gradient(135deg, #818cf8, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>LifeOS AI</h2>
    <p style='color: #64748b; font-size: 12px;'>Multi-Agent Personal Life OS</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "NAVIGATION MENU",
    [
        "🎯 Goal Planner & Dashboard",
        "📅 Today's Schedule",
        "🔥 Habit Tracker",
        "📚 Learning recommendations",
        "📋 Accountability Status",
        "📅 Weekly Reflections"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='font-size: 11px; color: #475569; text-align: center;'>
    Kaggle AI Agents Intensive Capstone Project<br>
    Track: Concierge Agents
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Stats Bar Helper
# ---------------------------------------------------------------------------
def render_stats_bar():
    goals_count = len(fetch_all("goals"))
    schedule_count = len(fetch_all("schedule"))
    habits_count = len(fetch_all("habits"))
    learning_count = len(fetch_all("learning"))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='stat-card stat-card-goals'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='stat-label'>Active Goals</div>
                <span style='font-size: 20px;'>🎯</span>
            </div>
            <div class='stat-val'>{goals_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='stat-card stat-card-schedule'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='stat-label'>Tasks Scheduled</div>
                <span style='font-size: 20px;'>📅</span>
            </div>
            <div class='stat-val'>{schedule_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='stat-card stat-card-habits'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='stat-label'>Habit Routines</div>
                <span style='font-size: 20px;'>🔥</span>
            </div>
            <div class='stat-val'>{habits_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='stat-card stat-card-learning'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='stat-label'>Learning Paths</div>
                <span style='font-size: 20px;'>📚</span>
            </div>
            <div class='stat-val'>{learning_count}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 1: Dashboard & Goal Input
# ---------------------------------------------------------------------------

if app_mode == "🎯 Goal Planner & Dashboard":
    st.markdown("<div class='main-header'>Goal Planner & Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Collaborative planning, scheduling, accountability, and reflections.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container(border=True):
            st.subheader("🎯 Submit New Long-Term Goal")
            
            goal_text = st.text_area("What is your high-level goal?", "Become a Senior Machine Learning Engineer in 180 Days", height=100)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                duration = st.number_input("Effort Days (Duration)", min_value=1, value=180)
            with col_t2:
                category = st.selectbox("Goal Category", ["learning", "health", "travel", "productivity"])
                
            submitter = st.text_input("User Email Address", "alice@company.com")
            target_date = st.date_input("Target Date")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Generate Personalized Life Plan", use_container_width=True, type="primary"):
                with st.spinner("Collaborative agents are planning, scheduling, and analyzing routines..."):
                    res = trigger_goal_workflow(
                        goal_text, duration, submitter, category, str(target_date)
                    )
                    if "error" in res:
                        st.error(f"Failed to submit goal: {res['error']}")
                    else:
                        st.success("Personalized life planning triggered successfully!")
                        time.sleep(1)
                        st.rerun()
 
    with col2:
        with st.container(border=True):
            st.subheader("✋ Requires Activation (Human-in-the-Loop)")
            
            pending = fetch_pending_sessions()
            if not pending:
                st.info("All clear! No pending goal plans require your activation.")
            else:
                for p in pending:
                    payload = p.get("payload") or {}
                    st.markdown(f"**Goal Target**: {payload.get('description', 'N/A')}")
                    st.write(f"**Effort Days**: `{payload.get('amount')}` | **Category**: `{payload.get('category')}`")
                    
                    review = p.get("review")
                    if review:
                        st.warning(f"**Agent Reflections & Insights**:\n{review}")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Activate Plan", key=f"act-{p['session_id']}", use_container_width=True, type="primary"):
                            res = resume_session(p['session_id'], p['interrupt_id'], True)
                            st.success("Goal Activated successfully!")
                            time.sleep(1)
                            st.rerun()
                    with col_btn2:
                        if st.button("Cancel Plan", key=f"can-{p['session_id']}", type="secondary", use_container_width=True):
                            res = resume_session(p['session_id'], p['interrupt_id'], False)
                            st.error("Goal plan cancelled.")
                            time.sleep(1)
                            st.rerun()
 
    # Display Goals history
    st.markdown("<div class='section-title'>Active Goals & Milestones Roadmap</div>", unsafe_allow_html=True)
    goals = fetch_all("goals")
    if not goals:
        st.info("No goals registered yet.")
    else:
        for r in goals:
            roadmap_text = r[2]
            roadmap_steps = []
            if roadmap_text:
                roadmap_text_stripped = roadmap_text.strip()
                if roadmap_text_stripped.startswith("{") or roadmap_text_stripped.startswith("["):
                    try:
                        parsed = json.loads(roadmap_text_stripped)
                        if isinstance(parsed, dict):
                            milestone_key = next((k for k in parsed if k.lower() == "milestones"), None)
                            steps_key = next((k for k in parsed if k.lower() == "steps"), None)
                            roadmap_key = next((k for k in parsed if k.lower() == "roadmap"), None)
                            
                            if milestone_key:
                                roadmap_steps = parsed[milestone_key]
                            elif steps_key:
                                roadmap_steps = parsed[steps_key]
                            elif roadmap_key:
                                r_val = parsed[roadmap_key]
                                if isinstance(r_val, list):
                                    roadmap_steps = r_val
                                else:
                                    roadmap_steps = [str(r_val)]
                            else:
                                roadmap_steps = [f"{k}: {v}" for k, v in parsed.items()]
                        elif isinstance(parsed, list):
                            roadmap_steps = parsed
                    except Exception:
                        pass
                
                if not roadmap_steps:
                    roadmap_steps = roadmap_text.split("\n")
                    
            with st.container(border=True):
                st.markdown(f"<h4 style='color: #a5b4fc; margin-top: 0; margin-bottom: 12px;'>🎯 {r[1]}</h4>", unsafe_allow_html=True)
                st.markdown("<p style='color: #e2e8f0; font-size: 14px;'><strong>Generated Roadmap:</strong></p>", unsafe_allow_html=True)
                for step in roadmap_steps:
                    if not step:
                        continue
                    if isinstance(step, dict):
                        days = step.get("Days", step.get("days", ""))
                        focus = step.get("Focus", step.get("focus", ""))
                        header = ""
                        if days or focus:
                            header = f"🗓️ <strong>{days}</strong> &mdash; <em>{focus}</em>"
                        else:
                            header = ", ".join([f"{k}: {v}" for k, v in step.items() if k.lower() not in ("tasks", "detailed_tasks")])
                        st.markdown(f"<div class='timeline-item' style='margin-bottom: 8px;'>{header}</div>", unsafe_allow_html=True)
                        
                        tasks_key = next((k for k in step if k.lower() in ("tasks", "detailed_tasks", "details")), None)
                        if tasks_key and isinstance(step[tasks_key], list):
                            for subtask in step[tasks_key]:
                                if subtask:
                                    st.markdown(f"<div style='margin-left: 25px; font-size: 13.5px; color: #cbd5e1; margin-bottom: 4px;'>• {subtask}</div>", unsafe_allow_html=True)
                    else:
                        if str(step).strip():
                            st.markdown(f"<div class='timeline-item'>{str(step).strip()}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top: 15px;'><small style='color: #64748b;'>Date Created: {r[3]}</small></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 2: Schedule
# ---------------------------------------------------------------------------

elif app_mode == "📅 Today's Schedule":
    st.markdown("<div class='main-header'>Today's Schedule & Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Daily calendar slots and priority tasks generated by the Time Manager.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    # Manual add schedule block
    with st.expander("➕ Add Task Schedule Block Manually"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            task_name = st.text_input("Task Title")
            time_block = st.text_input("Time Block Range", "09:00 AM - 10:30 AM")
        with col_s2:
            priority = st.selectbox("Priority Tier", ["High", "Medium", "Low"])
        if st.button("Add Task Block", use_container_width=True, type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO schedule (task_name, time_block, priority) VALUES (?, ?, ?)", (task_name, time_block, priority))
            conn.commit()
            conn.close()
            st.success("Task block added!")
            st.rerun()
            
    # Clear schedule
    if st.button("Clear Schedule List", type="secondary", use_container_width=True):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule")
        conn.commit()
        conn.close()
        st.success("Schedule cleared!")
        st.rerun()

    st.markdown("<div class='section-title'>Calendar Time-blocked Activities</div>", unsafe_allow_html=True)
    schedule = fetch_all("schedule")
    if not schedule:
        st.info("Your calendar schedule is currently empty.")
    else:
        for s in schedule:
            badge_class = "badge-high" if s[3] == "High" else ("badge-med" if s[3] == "Medium" else "badge-low")
            with st.container(border=True):
                col_left, col_right = st.columns([3, 1])
                with col_left:
                    st.markdown(f"<span class='badge {badge_class}'>{s[3]} Priority</span> <strong style='font-size: 16px; color:#f1f5f9;'>{s[1]}</strong>", unsafe_allow_html=True)
                with col_right:
                    st.markdown(f"<div style='text-align: right; color: #a5b4fc; font-weight: 600;'>⏰ {s[2]}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 3: Habit Tracker
# ---------------------------------------------------------------------------

elif app_mode == "🔥 Habit Tracker":
    st.markdown("<div class='main-header'>Habit Coach & Streaks</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Daily routines and streaking consistency indicators.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    with st.expander("➕ Register Habit Routine"):
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            h_name = st.text_input("Habit Description", "Daily DSA Practice")
            streak = st.number_input("Starting Streak (Days)", min_value=0, value=5)
        with col_h2:
            risk = st.selectbox("Consistency Risk Level", ["Low", "Medium", "High"])
        if st.button("Add Habit", use_container_width=True, type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO habits (habit_name, streak, risk_level) VALUES (?, ?, ?)", (h_name, streak, risk))
            conn.commit()
            conn.close()
            st.success("Habit routine registered!")
            st.rerun()

    st.markdown("<div class='section-title'>Active Habit Routines</div>", unsafe_allow_html=True)
    habits = fetch_all("habits")
    if not habits:
        st.info("No habit trackers active. Register a habit to start coaching!")
    else:
        for h in habits:
            badge_class = "badge-high" if h[3] == "High" else ("badge-med" if h[3] == "Medium" else "badge-low")
            with st.container(border=True):
                col_h_left, col_h_right = st.columns([3, 1])
                with col_h_left:
                    st.markdown(f"<h4 style='margin:0; color:#f1f5f9;'>🔥 {h[1]}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-top: 8px;'><span class='badge {badge_class}'>Risk: {h[3]}</span></div>", unsafe_allow_html=True)
                with col_h_right:
                    st.markdown(f"<div style='text-align: right;'><h3 style='margin:0; font-weight:800; color:#ec4899;'>{h[2]} Days</h3><small style='color:#64748b;'>Current Streak</small></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 4: Learning recommendations
# ---------------------------------------------------------------------------

elif app_mode == "📚 Learning recommendations":
    st.markdown("<div class='main-header'>Learning recommendations</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Curricula and resource recommendations generated by the Learning Agent.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    with st.expander("➕ Add Learning Path Recommendation"):
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            skill = st.text_input("Skill Gap Target", "DBMS Joins and Indexes")
            res_name = st.text_input("Recommended Resource Title", "LeetCode Database Track")
        with col_l2:
            act_type = st.selectbox("Activity Format", ["Course", "Book", "Project", "Practice"])
        if st.button("Save Recommendation", use_container_width=True, type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO learning (skill_gap, resource_name, activity_type) VALUES (?, ?, ?)", (skill, res_name, act_type))
            conn.commit()
            conn.close()
            st.success("Learning recommendation saved!")
            st.rerun()

    st.markdown("<div class='section-title'>Recommended Learning Resources</div>", unsafe_allow_html=True)
    learning = fetch_all("learning")
    if not learning:
        st.info("No learning paths generated yet.")
    else:
        for l in learning:
            with st.container(border=True):
                st.markdown(f"<h4 style='margin:0; color:#a5b4fc;'>📚 {l[2]}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:8px 0 0 0; color:#94a3b8; font-size:14px;'><strong>Skill Gap Target:</strong> {l[1]}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:4px 0 0 0; color:#64748b; font-size:12px;'>Activity Format: {l[3]}</p>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 5: Accountability Status
# ---------------------------------------------------------------------------

elif app_mode == "📋 Accountability Status":
    st.markdown("<div class='main-header'>Accountability Status</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Milestones progress and recovery plans.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    st.markdown("<div class='section-title'>Commitment Logs</div>", unsafe_allow_html=True)
    acc = fetch_all("accountability")
    if not acc:
        st.info("Accountability reports will appear here when a goal is activated.")
    else:
        for a in acc:
            with st.container(border=True):
                st.markdown(f"<h4 style='margin:0; color:#f1f5f9;'>📋 Status: {a[1]}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:8px 0 0 0; color:#e2e8f0;'><strong>Missed Milestones:</strong> {a[2]}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:4px 0 0 0; color:#94a3b8;'><strong>Recovery Plan:</strong> {a[3]}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top: 10px;'><small style='color: #64748b;'>Logged: {a[4]}</small></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App Page 6: Weekly Reflections
# ---------------------------------------------------------------------------

elif app_mode == "📅 Weekly Reflections":
    st.markdown("<div class='main-header'>Weekly Reflections & Insights</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Summaries and performance insights generated by the Reflection Agent.</div>", unsafe_allow_html=True)
    
    render_stats_bar()
    
    st.markdown("<div class='section-title'>Reflective Coaching Summaries</div>", unsafe_allow_html=True)
    reflections = fetch_all("reflections")
    if not reflections:
        st.info("Weekly reflection reports will appear here as goals progress.")
    else:
        for r in reflections:
            with st.container(border=True):
                st.markdown(f"<h4 style='margin:0; color:#f472b6;'>📅 Period: {r[1]}</h4>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:10px; color:#e2e8f0; font-size:14px; line-height:1.6;'><strong>Performance Summary:</strong><br>{r[2]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:8px; color:#a5b4fc; font-size:14px; line-height:1.6;'><strong>Productivity Insights:</strong><br>{r[3]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top: 10px;'><small style='color: #64748b;'>Reflected: {r[4]}</small></div>", unsafe_allow_html=True)
