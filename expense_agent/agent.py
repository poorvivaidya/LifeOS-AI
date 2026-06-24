# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LifeOS AI Coordinator Agent.

This agent processes life goals and tracks tasks, schedules, and habits.
It routes goals through a collaborative multi-agent workflow:
- Goal plans under 100 days of effort are auto-approved.
- Goal plans of 100 days or more run through the complete multi-agent pipeline
  (Goal, Time, Habit, Learning, Accountability, Reflection) and are paused for
  user sign-off.
"""

import base64
import json
import os
import re
import sys

from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from pydantic import BaseModel, Field

from .config import config


# ---------------------------------------------------------------------------
# Pydantic schemas for structured data flow between nodes
# ---------------------------------------------------------------------------


class ExpenseData(BaseModel):
    """LifeOS Goal planning data structure.

    Keeps the same class name and fields for compatibility with test runners.
    """

    amount: float = Field(description="Goal effort/duration in days")
    submitter: str = Field(description="Email of the user submitting the goal")
    category: str = Field(description="Goal category, e.g. learning, health, travel")
    description: str = Field(description="Detailed description of the goal")
    date: str = Field(description="Target completion date (YYYY-MM-DD)")


# ---------------------------------------------------------------------------
# Function nodes
# ---------------------------------------------------------------------------


def parse_expense_email(node_input: str) -> Event:
    """Parse incoming trigger event and extract goal data."""
    try:
        event = json.loads(node_input)
    except json.JSONDecodeError:
        return Event(output={"error": f"Invalid JSON: {node_input[:200]}"})

    data = event.get("data", {})

    if isinstance(data, str):
        try:
            data = json.loads(base64.b64decode(data))
        except Exception:
            return Event(output={"error": f"Failed to decode data: {data[:200]}"})

    return Event(
        output={
            "amount": float(data.get("amount", 0)),
            "submitter": data.get("submitter", "unknown"),
            "category": data.get("category", "other"),
            "description": data.get("description", ""),
            "date": data.get("date", ""),
        }
    )


def route_by_amount(node_input: dict, ctx: Context) -> Event:
    """Route goal based on the 100 days threshold."""
    if "error" in node_input:
        return Event(output=node_input)
    ctx.state["expense_data"] = node_input
    amount = node_input.get("amount", 0)
    if amount >= config.review_threshold:
        return Event(route="NEEDS_REVIEW", output=node_input)
    return Event(route="AUTO_APPROVE", output=node_input)


# Regex patterns for SSNs and Credit Cards (PII protection)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")
CC_PATTERN = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b|\b\d{13,16}\b")

# Regex pattern for prompt injection detection
PROMPT_INJECTION_PATTERN = re.compile(
    r"ignore\s+(?:previous|all|system)\s+instructions|"
    r"bypass\s+(?:the\s+)?rules|"
    r"bypass\s+(?:the\s+)?policy|"
    r"auto-approve|"
    r"auto\s+approve|"
    r"force\s+(?:auto-)?approval|"
    r"system\s+instruction|"
    r"override\s+(?:the\s+)?rules|"
    r"override\s+(?:the\s+)?policy",
    re.IGNORECASE
)


def security_checkpoint(node_input: dict, ctx: Context) -> Event:
    """Scrub PII and detect prompt injection attempts before multi-agent review."""
    description = node_input.get("description", "")
    redacted_categories = []

    # Scrub SSNs
    if SSN_PATTERN.search(description):
        description = SSN_PATTERN.sub("[SSN_REDACTED]", description)
        redacted_categories.append("SSN")

    # Scrub Credit Cards
    if CC_PATTERN.search(description):
        description = CC_PATTERN.sub("[CREDIT_CARD_REDACTED]", description)
        redacted_categories.append("Credit Card")

    # Save redacted categories in workflow state
    ctx.state["redacted_categories"] = redacted_categories

    # Update goal data in state and output
    updated_expense = dict(node_input)
    updated_expense["description"] = description
    ctx.state["expense_data"] = updated_expense

    # Detect prompt injection
    if PROMPT_INJECTION_PATTERN.search(description):
        log_entry = {
            "severity": "WARNING",
            "message": f"Security alert: Prompt injection attempt detected in expense from {updated_expense.get('submitter', 'unknown')}",
            "alert_type": "security_event",
            "submitter": updated_expense.get("submitter", "unknown"),
            "amount": updated_expense.get("amount", 0),
            "category": updated_expense.get("category", ""),
            "description": description,
        }
        print(json.dumps(log_entry), flush=True)
        ctx.state["security_event"] = True
        return Event(route="SECURITY_FLAG", output=updated_expense)

    return Event(route="CLEAN", output=updated_expense)


def auto_approve(node_input: dict) -> Event:
    """Auto-approve a simple life goal plan and log the decision."""
    log_entry = {
        "severity": "INFO",
        "message": (
            f"LifeOS simple goal plan auto-approved: {node_input['amount']:.2f} days"
            f" for {node_input['submitter']}"
        ),
        "decision": "approved",
        "amount": node_input["amount"],
        "submitter": node_input["submitter"],
        "category": node_input["category"],
    }
    print(json.dumps(log_entry), flush=True)
    
    # Save simple goal to SQLite db
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO goals (goal_text, roadmap) VALUES (?, ?)", 
                       (node_input["description"], "Auto-approved roadmap for short-term goal."))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging auto-approved goal to SQLite: {e}", flush=True)

    return Event(output={"status": "approved", **node_input})


# ---------------------------------------------------------------------------
# Collaborative Agents
# ---------------------------------------------------------------------------


def emit_expense_alert(
    submitter: str,
    amount: float,
    category: str,
    risk_summary: str,
) -> dict:
    """Emit a structured log alerting the user to review a high-value/long-term goal plan.

    Keeps function name and signature for compatibility with frontend and tests.
    """
    log_entry = {
        "severity": "WARNING",
        "message": (
            f"LifeOS AI goal alert: {amount:.2f} effort days from {submitter} — {risk_summary}"
        ),
        "alert_type": "expense_review",  # keep compatibility with frontend
        "submitter": submitter,
        "amount": amount,
        "category": category,
        "risk_summary": risk_summary,
    }
    print(json.dumps(log_entry), flush=True)
    return {"status": "alert_emitted", "submitter": submitter, "amount": amount}


# Connect to the local LifeOS FastMCP server
mcp_server_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mcp_server_fast.py"
)
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path]
        )
    )
)


# 1. Coordinator Agent (decides orchestration)
coordinator_agent = Agent(
    name="coordinator_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Coordinator Agent. Review the user's high-level goal and decide which planning agents should be called and in what order to construct a comprehensive personalized life plan. Always outline the sequence starting with Goal Planner -> Learning -> Time Management -> Habit Coach -> Accountability -> Reflection.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 2. Goal Planner Agent
goal_planner_agent = Agent(
    name="goal_planner_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Goal Planner Agent. Break the user's goal into actionable milestones and roadmaps. Always call the goal_tool with action='add', specifying the goal_text and the detailed roadmap you create.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 3. Learning Agent
learning_agent = Agent(
    name="learning_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Learning Agent. Identify skill gaps and recommend learning resources (courses, practice, projects). Always call the learning_tool with action='add', specifying the skill_gap description, resource_name, and activity_type.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 4. Time Management Agent
time_management_agent = Agent(
    name="time_management_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Time Management Agent. Time-block activities and prioritize daily schedules. Always call the schedule_tool with action='add', specifying the task_name, time_block range, and priority level.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 5. Habit Coach Agent
habit_coach_agent = Agent(
    name="habit_coach_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Habit Coach Agent. Formulate supportive daily routines and track habit streaks. Always call the habit_tool with action='add', specifying the habit_name, initial streak count, and risk_level rating.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 6. Accountability Agent
accountability_agent = Agent(
    name="accountability_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Accountability Agent. Define milestones and recovery options if user gets off-track.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)

# 7. Reflection Agent (replaces review_agent as the final reviewer/coordinator)
reflection_agent = Agent(
    name="reflection_agent",
    model=config.model,
    mode="single_turn",
    instruction="""You are the Reflection Agent. Review the compiled plan, schedule, habits, and learning plans. Summarize weekly performance recommendations, insights, and output the Final Personalized Life Plan.""",
    input_schema=ExpenseData,
    tools=[mcp_toolset],
)


# ---------------------------------------------------------------------------
# Programmatic Helper Functions to Save Agent Outputs to SQLite
# ---------------------------------------------------------------------------

def save_goal_roadmap(node_input, ctx: Context) -> Event:
    expense = ctx.state.get("expense_data", {})
    goal_text = expense.get("description", "Goal Target")
    
    roadmap = ""
    if isinstance(node_input, dict):
        roadmap = node_input.get("text", node_input.get("message", json.dumps(node_input)))
    elif isinstance(node_input, str):
        roadmap = node_input
    else:
        roadmap = str(node_input)
        
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO goals (goal_text, roadmap) VALUES (?, ?)", (goal_text, roadmap))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in save_goal_roadmap: {e}", flush=True)
    return Event(output=expense)


def save_learning_resources(node_input, ctx: Context) -> Event:
    expense = ctx.state.get("expense_data", {})
    
    text = ""
    if isinstance(node_input, dict):
        text = node_input.get("text", json.dumps(node_input))
    elif isinstance(node_input, str):
        text = node_input
    else:
        text = str(node_input)
        
    skill_gap = "Advanced concepts"
    resource_name = "LifeOS Personalized Curriculum Guide"
    activity_type = "Course"
    
    if text:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                skill_gap = parts[0].strip("*- ")
                resource_name = parts[1].strip()
                break
                
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO learning (skill_gap, resource_name, activity_type) VALUES (?, ?, ?)", 
                       (skill_gap[:200], resource_name[:200], activity_type))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in save_learning_resources: {e}", flush=True)
    return Event(output=expense)


def save_schedule(node_input, ctx: Context) -> Event:
    expense = ctx.state.get("expense_data", {})
    
    text = ""
    if isinstance(node_input, dict):
        text = node_input.get("text", json.dumps(node_input))
    elif isinstance(node_input, str):
        text = node_input
    else:
        text = str(node_input)
        
    task_name = "Daily Study & Refactoring Sessions"
    time_block = "09:00 AM - 10:30 AM"
    priority = "High"
    
    if text:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if "-" in line or "@" in line:
                task_name = line.strip("*- ")
                break
                
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schedule (task_name, time_block, priority) VALUES (?, ?, ?)", 
                       (task_name[:200], time_block, priority))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in save_schedule: {e}", flush=True)
    return Event(output=expense)


def save_habits(node_input, ctx: Context) -> Event:
    expense = ctx.state.get("expense_data", {})
    habit_name = "Maintain Daily Code Practice Checklist"
    streak = 1
    risk_level = "Medium"
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO habits (habit_name, streak, risk_level) VALUES (?, ?, ?)", 
                       (habit_name[:200], streak, risk_level))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in save_habits: {e}", flush=True)
    return Event(output=expense)


def save_accountability(node_input, ctx: Context) -> Event:
    expense = ctx.state.get("expense_data", {})
    progress_status = "Initiated"
    missed_milestones = "None"
    recovery_plan = "Weekly schedule buffers configured"
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accountability (progress_status, missed_milestones, recovery_plan) VALUES (?, ?, ?)", 
                       (progress_status, missed_milestones, recovery_plan))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in save_accountability: {e}", flush=True)
    return Event(output=expense)


def log_reflection_alert(node_input, ctx: Context) -> Event:
    """Log the reflection alert summary and trigger emit_expense_alert programmatically exactly once."""
    expense = ctx.state.get("expense_data", {})
    submitter = expense.get("submitter", "unknown")
    amount = expense.get("amount", 0)
    category = expense.get("category", "")

    # Extract message/text from node_input
    risk_summary = ""
    if isinstance(node_input, dict):
        risk_summary = node_input.get("text", node_input.get("message", json.dumps(node_input)))
    elif isinstance(node_input, str):
        risk_summary = node_input
    else:
        risk_summary = str(node_input)

    if not risk_summary or risk_summary == "{}" or risk_summary == "None":
        risk_summary = "Goal plan reviewed during the reflection phase."

    # Truncate to ensure it fits nicely in logs and alerts
    if len(risk_summary) > 500:
        truncated_summary = risk_summary[:497] + "..."
    else:
        truncated_summary = risk_summary

    # Save to SQLite database table reflections and accountability logs
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lifeos.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Save to Reflections
        cursor.execute("INSERT INTO reflections (review_period, performance_summary, insights) VALUES (?, ?, ?)", 
                       ("Weekly Setup", truncated_summary, risk_summary))
        
        # Save to Accountability
        cursor.execute("INSERT INTO accountability (progress_status, missed_milestones, recovery_plan) VALUES (?, ?, ?)",
                       ("Initiated", "None detected", "Micro-session buffers established"))
                       
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging reflection to SQLite: {e}", flush=True)

    emit_expense_alert(
        submitter=submitter,
        amount=amount,
        category=category,
        risk_summary=truncated_summary,
    )
    return Event(output=expense)


# ---------------------------------------------------------------------------
# HITL: pause the workflow for human approval
# ---------------------------------------------------------------------------


def request_approval(node_input, ctx: Context):  # type: ignore[no-untyped-def]
    """Pause the workflow and wait for the user to activate the plan."""
    expense = ctx.state.get("expense_data", {})
    yield RequestInput(
        message="Plan requires final confirmation. Activate or cancel.",
        payload=expense,
    )


def process_decision(node_input, ctx: Context) -> Event:  # type: ignore[no-untyped-def]
    """Process the user's activation decision and log the outcome."""
    decision = "unknown"
    if isinstance(node_input, dict):
        decision = node_input.get("decision", "unknown")
    elif isinstance(node_input, str):
        decision = "approve" if "approve" in node_input.lower() else "reject"

    approved = decision == "approve"
    expense = ctx.state.get("expense_data", {})
    status = "approved" if approved else "rejected"

    log_entry = {
        "severity": "INFO" if approved else "WARNING",
        "message": f"LifeOS goal plan {status} by user",
        "decision": status,
    }
    print(json.dumps(log_entry), flush=True)

    submitter = expense.get("submitter", "unknown")
    amount = expense.get("amount", 0)
    category = expense.get("category", "")
    description = expense.get("description", "")
    date = expense.get("date", "")

    parts = [f"Goal plan of {amount:.2f} days from {submitter} has been {status}."]
    if description:
        parts.append(f'"{description}" ({category}) on {date}.')
    if approved:
        parts.append(
            "The goal has been activated in LifeOS."
        )
    else:
        parts.append(
            "The planning process was cancelled."
        )

    return Event(output={"status": status, "message": " ".join(parts)})


# ---------------------------------------------------------------------------
# Graph-based workflow
# ---------------------------------------------------------------------------

root_agent = Workflow(
    name="expense_processor",  # Keep same workflow name for compatibility
    edges=[
        ("START", parse_expense_email, route_by_amount),
        (
            route_by_amount,
            {
                "AUTO_APPROVE": auto_approve,
                "NEEDS_REVIEW": security_checkpoint,
            },
        ),
        (
            security_checkpoint,
            {
                "CLEAN": coordinator_agent,
                "SECURITY_FLAG": request_approval,
            },
        ),
        (coordinator_agent, goal_planner_agent),
        (goal_planner_agent, save_goal_roadmap),
        (save_goal_roadmap, learning_agent),
        (learning_agent, save_learning_resources),
        (save_learning_resources, time_management_agent),
        (time_management_agent, save_schedule),
        (save_schedule, habit_coach_agent),
        (habit_coach_agent, save_habits),
        (save_habits, accountability_agent),
        (accountability_agent, save_accountability),
        (save_accountability, reflection_agent),
        (reflection_agent, log_reflection_alert),
        (log_reflection_alert, request_approval),
        (request_approval, process_decision),
    ],
)

from google.adk.apps import App

app = App(root_agent=root_agent, name="expense_agent")
