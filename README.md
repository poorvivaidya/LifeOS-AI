# LifeOS AI – A Multi-Agent Personal Life Operating System

LifeOS AI is a production-grade multi-agent personal Life Operating System built as a Capstone project for the **Kaggle AI Agents Intensive Vibe Coding Capstone Project (Concierge Track)**. 

The platform helps users manage long-term goals, calendar schedules, habit tracking, personalized learning plans, and reflective coaching through a team of 7 specialized AI agents orchestrated by an **ADK 2.0 graph-based workflow** with SQLite persistence and a premium Streamlit dashboard.

<table>
  <thead>
    <tr>
      <th colspan="2">Key Features</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🔄</td>
      <td><strong>ADK 2.0 Multi-Agent Workflow:</strong> Conditional routing orchestrating 7 collaborative agents (Coordinator, Goal Planner, Learning, Time Management, Habit Coach, Accountability, and Reflection).</td>
    </tr>
    <tr>
      <td>🔌</td>
      <td><strong>FastMCP Server Integration:</strong> Custom SQLite database management tools exposed over stdio via FastMCP.</td>
    </tr>
    <tr>
      <td>🗄️</td>
      <td><strong>SQLite Local Persistence:</strong> Structured database tracking of goals, milestones, schedules, habit streaks, recommended learning paths, accountability logs, and weekly reviews.</td>
    </tr>
    <tr>
      <td>✋</td>
      <td><strong>Human-in-the-Loop (HITL):</strong> Major goal plans (>= 100 days duration) pause the workflow using <code>RequestInput</code> until the user explicitly reviews and activates/cancels the plan.</td>
    </tr>
    <tr>
      <td>🖥️</td>
      <td><strong>Streamlit Dashboard UI:</strong> A modern, responsive dark-mode productivity dashboard to submit goals, view daily schedules, track habits, access curricula, and read agent reflection summaries.</td>
    </tr>
  </tbody>
</table>

---

## System Architecture

```
                       [ Goal Submitted ]
                               │
                 parse_expense_email (Goal parsing)
                               │
                       route_by_amount
                        │            │
                    < 100 days    >= 100 days
                        │            │
                  auto_approve   security_checkpoint (PII & Injection checks)
                   (SQLite write)    │
                                 coordinator_agent
                                     │
                                 goal_planner_agent (milestones & roadmaps)
                                     │
                                 learning_agent (skill gap & resources)
                                     │
                                 time_management_agent (calendar slots)
                                     │
                                 habit_coach_agent (routines & streaks)
                                     │
                                 accountability_agent (milestones review)
                                     │
                                 reflection_agent (insights summary)
                                     │
                                 log_reflection_alert (SQLite reflection write)
                                     │
                                 request_approval (HITL pause)
                                     │
                                 process_decision (Activate / Cancel)
```

### Specialized Core Agents
1. **Coordinator Agent**: Orchestrates workflow routing.
2. **Goal Planner Agent**: Translates high-level goals into roadmaps and milestones.
3. **Learning Agent**: Assesses skill gaps and recommends online/offline resources.
4. **Time Management Agent**: Allocates time blocks and prioritize calendar slots.
5. **Habit Coach Agent**: Regulates routines, sets risk levels, and updates habit streaks.
6. **Accountability Agent**: Measures progress milestones and constructs recovery paths.
7. **Reflection Agent**: Compiles final plan summaries, weekly performance reflections, and coaching insights.

---

## Database Schema (SQLite)

The agent interacts with the SQLite database file `lifeos.db` using the following schema:
* `goals`: Stores the parsed goal descriptions and their multi-step roadmaps.
* `schedule`: Manages the daily time-blocked slots and tasks, filtered by priority (High, Medium, Low).
* `habits`: Tracks habit streaking, descriptions, and consistency risks.
* `learning`: Lists skill gaps and recommended learning resources/activities.
* `accountability`: Tracks overall milestone completion and recovery plans.
* `reflections`: Holds weekly reviews, performance summaries, and productivity insights.

---

## Getting Started

### Prerequisites
* Python 3.11+
* [uv](https://github.com/astral-sh/uv) package manager installed

### 1. Install Dependencies
Run `uv sync` to sync workspace packages.

### 2. Start the FastMCP Server & ADK Backend
Run the backend server on port 8080. This hosts the ADK 2.0 REST API endpoints, security layers, and coordinates the FastMCP subprocess:
```bash
uv run python expense_agent/fast_api_app.py
```

### 3. Launch the Streamlit Dashboard UI
In a separate terminal, launch the Streamlit frontend:
```bash
uv run streamlit run streamlit_app.py --server.port 8083
```
Open `http://localhost:8083` in your browser.

---

## Verification & Tests

### Automated Test Suite
To verify the compatibility of the multi-agent graph, trigger routes, and PII/prompt injection defenses, run the integration and unit tests:
```bash
uv run pytest
```
*Output should show all 10/10 tests passing cleanly.*

### Manual Walkthrough
1. Navigate to the **Streamlit Dashboard** (`http://localhost:8083`).
2. Go to the **Goal Planner** tab, enter a goal (e.g. *Become a Backend Engineer in 120 Days*), and hit **Generate Plan**.
3. Under the **Requires User Confirmation** column, inspect the compiled reflections and click **Activate Plan**.
4. Explore the other tabs (Today's Schedule, Habit Tracker, Learning Recommendations, Reflections) to inspect the SQLite-persisted agent outputs.

---

## Media Showcase Gallery

### 🎯 Goal Planner & Active Roadmap Dashboard
![LifeOS AI Dashboard](./media/lifeos_goals_dashboard.png)

### 📅 Today's Schedule & Time-blocked Calendar
![LifeOS AI Schedule](./media/lifeos_schedule.png)

### 🔥 Habit Tracker & Streak Analytics
![LifeOS AI Habits](./media/lifeos_habits.png)

### 📚 Skill Gaps & Personalized Learning Curricula
![LifeOS AI Learning](./media/lifeos_learning.png)

### 📋 Accountability Checkpoints & Status Logs
![LifeOS AI Accountability](./media/lifeos_accountability.png)

### 📅 Weekly Reflections & Coach Insights
![LifeOS AI Reflections](./media/lifeos_reflections.png)

### ✋ Requires Activation Card (Human-in-the-Loop)
![LifeOS AI HITL Activation](./media/lifeos_dashboard_pending.png)

