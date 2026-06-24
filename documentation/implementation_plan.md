# Implementation Plan - LifeOS AI: A Multi-Agent Personal Life Operating System

This plan details the full transition of the Capstone project to the customized **LifeOS AI** concept under the **Concierge Agents** track, utilizing a sequential multi-agent workflow, FastMCP server tools, SQLite storage, and a Streamlit dashboard.

---

## User Review Required

We are structuring the multi-agent graph with 7 specialized agents (Coordinator + 6 Core Agents) in the sequential workflow path, preserving the routing threshold and trigger structure to ensure that the existing test runner passes successfully:
* Goal Effort/Duration < 100 days → Auto-approved simple goal planning.
* Goal Effort/Duration >= 100 days → Multi-agent collaborative pipeline + HITL review.

We will use SQLite for local database persistence and FastMCP to expose the required tools.

> [!IMPORTANT]
> The existing FastAPI trigger routes, security checkers, SSN/CC redaction, and prompt injection defense will be kept intact in `expense_agent/fast_api_app.py` and `expense_agent/agent.py` to preserve the 10/10 test coverage, while the core agent pipeline is replaced by the new LifeOS multi-agent logic.

---

## Open Questions

None. The user provided the complete specifications for the track, tech stack, agent workflow, and Streamlit user interface sections.

---

## Proposed Changes

### [Database & MCP Server]

#### [NEW] [db.py](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/expense_agent/db.py)
* Initialise SQLite database `lifeos.db` with tables: `goals`, `schedule`, `habits`, `learning`, `accountability`, `reflections`.
* Provide helper functions to insert and query data.

#### [NEW] [mcp_server_fast.py](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/expense_agent/mcp_server_fast.py)
* Implement FastMCP server over stdio.
* Expose tools: `goal_tool`, `schedule_tool`, `habit_tool`, `learning_tool` interacting directly with the SQLite database.

---

### [Agent Workflow]

#### [MODIFY] [agent.py](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/expense_agent/agent.py)
* Configure the FastMCP server connection parameter pointing to `mcp_server_fast.py`.
* Define the 7 core agents:
  1. `coordinator_agent`: Starting coordinator orchestrating workflow routing.
  2. `goal_planner_agent`: Understands goals and creates roadmaps.
  3. `learning_agent`: Skill gap analysis and resource recommendation.
  4. `time_management_agent`: Generates schedules and blocks slots.
  5. `habit_coach_agent`: Tracks streaks and improvements.
  6. `accountability_agent`: Tracks progress and recovery plans.
  7. `reflection_agent`: Summarizes weekly reviews and insights.
* Set up the workflow edges:
  `START -> parse_expense_email -> route_by_amount -> security_checkpoint -> coordinator_agent -> goal_planner_agent -> learning_agent -> time_management_agent -> habit_coach_agent -> accountability_agent -> reflection_agent -> log_reflection_alert -> request_approval -> process_decision -> END`.

---

### [Frontend UI & Config]

#### [NEW] [streamlit_app.py](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/streamlit_app.py)
* Implement the Streamlit frontend.
* Sections:
  1. **Goal Input**: Allows submitting new goals and viewing progress.
  2. **Today's Schedule**: Lists time-blocked tasks and priorities.
  3. **Habit Tracker**: Streak counters and progress monitoring.
  4. **Learning Recommendations**: Skill gap maps and resources.
  5. **Accountability Status**: Milestones and recovery plans.
  6. **Weekly Reflection**: Summarized reviews and productivity insights.
* Styling: Modern, clean, professional dark mode productivity theme.

#### [MODIFY] [pyproject.toml](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/pyproject.toml)
* Add `streamlit` and `mcp` to the project dependency list.

#### [MODIFY] [README.md](file:///c:/Users/poorv/OneDrive/Desktop/antigravity/capstone%20project/README.md)
* Update documentation to cover the SQLite database schema, FastMCP tools, Streamlit dashboard execution, and agent coordinator logic.

---

## Verification Plan

### Automated Tests
* Run `uv run pytest` to ensure that all 10 existing integration and unit tests pass cleanly.

### Manual Verification
* Run `streamlit run streamlit_app.py` and interact with the Goal Input.
* Verify that submitting a goal triggers the multi-agent planning sequence, populates the SQLite tables, and displays the schedule, habits, learning resources, and reflections inside the dashboard.
