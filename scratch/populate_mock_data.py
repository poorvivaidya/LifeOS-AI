import sqlite3
import os
import sys

# Add project root to python path to import from expense_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from expense_agent.db import init_db, DB_PATH

def populate_data():
    # Initialize database tables
    print("Initializing database tables...")
    init_db()
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Clear existing data to avoid duplicates
    tables = ['goals', 'schedule', 'habits', 'learning', 'accountability', 'reflections']
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
    
    # 2. Insert goals
    goals_data = [
        ("Become a Senior Machine Learning Engineer in 180 Days", "Milestone 1: Math & Statistics (Days 1-30)\nMilestone 2: Classical ML & Deep Learning Foundations (Days 31-90)\nMilestone 3: System Design & MLOps deployment (Days 91-150)\nMilestone 4: Capstone projects & mock interviews (Days 151-180)"),
        ("Run a Full Marathon in 6 Months", "Milestone 1: 5K base building (Weeks 1-4)\nMilestone 2: 10K endurance training (Weeks 5-10)\nMilestone 3: Half-marathon run (Week 12)\nMilestone 4: Peak mileage & 32K long run (Weeks 13-20)\nMilestone 5: Marathon race day (Week 24)")
    ]
    cursor.executemany("INSERT INTO goals (goal_text, roadmap) VALUES (?, ?)", goals_data)
    
    # 3. Insert schedule
    schedule_data = [
        ("Implement Multi-Agent Graph Router", "09:00 AM - 10:30 AM", "High"),
        ("System Architecture Review", "11:00 AM - 12:30 PM", "Medium"),
        ("Leisure: Evening Cardio Run", "06:00 PM - 07:00 PM", "Low"),
        ("DSA: LeetCode Daily Challenge", "08:00 PM - 09:30 PM", "High")
    ]
    cursor.executemany("INSERT INTO schedule (task_name, time_block, priority) VALUES (?, ?, ?)", schedule_data)
    
    # 4. Insert habits
    habits_data = [
        ("Daily DSA Practice", 18, "Low"),
        ("8 Hours Sleep Schedule", 5, "High"),
        ("Coding without distraction", 12, "Medium"),
        ("Healthy Diet Maintenance", 22, "Low")
    ]
    cursor.executemany("INSERT INTO habits (habit_name, streak, risk_level) VALUES (?, ?, ?)", habits_data)
    
    # 5. Insert learning
    learning_data = [
        ("System Design: Distributed Caching", "Designing Data-Intensive Applications (Book)", "Book"),
        ("MLOps: Kubernetes deployment", "GCP Vertex AI pipelines walkthrough", "Practice"),
        ("Advanced Python: AsyncIO", "Python documentation & RealPython tutorials", "Course")
    ]
    cursor.executemany("INSERT INTO learning (skill_gap, resource_name, activity_type) VALUES (?, ?, ?)", learning_data)
    
    # 6. Insert accountability
    accountability_data = [
        ("Initiated", "None detected", "Weekly buffer slot allocated on Sundays"),
        ("On Track", "Missed Tuesday gym session", "Rescheduled to Saturday morning")
    ]
    cursor.executemany("INSERT INTO accountability (progress_status, missed_milestones, recovery_plan) VALUES (?, ?, ?)", accountability_data)
    
    # 7. Insert reflections
    reflections_data = [
        ("Week 1 Review", "Successfully completed 4 LeetCode hard problems and built the SQLite manager database schema.", "Productivity is peak in morning hours. Need to sleep early to support 8-hour target."),
        ("Week 2 Review", "Struggled with MLOps configuration due to dependencies, but finished classical ML refresher.", "Break complex setups into smaller isolation steps rather than building all at once.")
    ]
    cursor.executemany("INSERT INTO reflections (review_period, performance_summary, insights) VALUES (?, ?, ?)", reflections_data)
    
    conn.commit()
    print("Database populated successfully with mock data!")
    conn.close()

if __name__ == "__main__":
    populate_data()
