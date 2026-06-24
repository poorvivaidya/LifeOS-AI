import os
import sqlite3
from mcp.server.fastmcp import FastMCP

# Define FastMCP server
mcp = FastMCP("LifeOS-MCP-Server")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lifeos.db")

@mcp.tool()
def goal_tool(action: str, goal_text: str = None, roadmap: str = None) -> str:
    """Manage user goals in the database.
    
    Args:
        action: The database action to perform ('add', 'get_latest', or 'list').
        goal_text: Optional goal description text to insert.
        roadmap: Optional goal roadmap/milestones JSON or text representation.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if action == "add" and goal_text:
        cursor.execute("INSERT INTO goals (goal_text, roadmap) VALUES (?, ?)", (goal_text, roadmap))
        conn.commit()
        res = "Goal added successfully."
    elif action == "get_latest":
        cursor.execute("SELECT goal_text, roadmap FROM goals ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        res = f"Latest Goal: {row[0]}\nRoadmap: {row[1]}" if row else "No goals found."
    else:
        cursor.execute("SELECT id, goal_text, roadmap FROM goals ORDER BY id DESC")
        rows = cursor.fetchall()
        res = "\n".join([f"ID {r[0]}: {r[1]} - Roadmap: {r[2]}" for r in rows])
    conn.close()
    return res

@mcp.tool()
def schedule_tool(action: str, task_name: str = None, time_block: str = None, priority: str = None) -> str:
    """Manage schedule blocks in the database.
    
    Args:
        action: The database action to perform ('add', 'list', or 'clear').
        task_name: Optional task name to add.
        time_block: Optional time range (e.g. '09:00 - 10:00').
        priority: Optional priority tier ('High', 'Medium', 'Low').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if action == "add" and task_name and time_block:
        cursor.execute("INSERT INTO schedule (task_name, time_block, priority) VALUES (?, ?, ?)", (task_name, time_block, priority or 'Medium'))
        conn.commit()
        res = "Schedule block added."
    elif action == "clear":
        cursor.execute("DELETE FROM schedule")
        conn.commit()
        res = "Schedule cleared."
    else:
        cursor.execute("SELECT task_name, time_block, priority FROM schedule")
        rows = cursor.fetchall()
        res = "\n".join([f"[{priority}] {task_name} @ {time_block}" for task_name, time_block, priority in rows])
    conn.close()
    return res

@mcp.tool()
def habit_tool(action: str, habit_name: str = None, streak: int = 0, risk_level: str = 'Low') -> str:
    """Manage habits and streak trackers.
    
    Args:
        action: The database action to perform ('add', 'update_streak', or 'list').
        habit_name: Optional habit name to add or modify.
        streak: Optional streak counter value in days.
        risk_level: Optional risk rating for habit consistency ('Low', 'Medium', 'High').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if action == "add" and habit_name:
        cursor.execute("INSERT INTO habits (habit_name, streak, risk_level) VALUES (?, ?, ?)", (habit_name, streak, risk_level))
        conn.commit()
        res = "Habit registered."
    elif action == "update_streak" and habit_name:
        cursor.execute("UPDATE habits SET streak = ? WHERE habit_name = ?", (streak, habit_name))
        conn.commit()
        res = "Habit streak updated."
    else:
        cursor.execute("SELECT habit_name, streak, risk_level FROM habits")
        rows = cursor.fetchall()
        res = "\n".join([f"{habit_name}: Streak = {streak} days, Risk = {risk_level}" for habit_name, streak, risk_level in rows])
    conn.close()
    return res

@mcp.tool()
def learning_tool(action: str, skill_gap: str = None, resource_name: str = None, activity_type: str = None) -> str:
    """Manage skill gap analyses and educational recommendations.
    
    Args:
        action: The database action to perform ('add' or 'list').
        skill_gap: Optional description of the user's current skill gap.
        resource_name: Optional recommended course or reading resource.
        activity_type: Optional activity format ('Course', 'Book', 'Project', 'Practice').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if action == "add" and skill_gap and resource_name:
        cursor.execute("INSERT INTO learning (skill_gap, resource_name, activity_type) VALUES (?, ?, ?)", (skill_gap, resource_name, activity_type or 'Course'))
        conn.commit()
        res = "Learning recommendation added."
    else:
        cursor.execute("SELECT skill_gap, resource_name, activity_type FROM learning")
        rows = cursor.fetchall()
        res = "\n".join([f"Gap: {skill_gap} -> Resource: {resource_name} ({activity_type})" for skill_gap, resource_name, activity_type in rows])
    conn.close()
    return res

if __name__ == "__main__":
    mcp.run()
