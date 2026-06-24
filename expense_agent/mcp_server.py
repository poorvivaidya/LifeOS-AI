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

"""Local MCP Server exposing LifeOS AI database and scheduling tools for collaborative agents."""

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("LifeOSLookup")


@mcp.tool()
def get_user_schedule_conflicts(member_email: str, category: str) -> str:
    """Check if the user has scheduling conflicts or busy slots for a given category/topic.

    Args:
        member_email: The email address of the user.
        category: The category of the goal (e.g. learning, career, health, travel).
    """
    # Mock schedule conflict database
    database = {
        "alice@company.com": {
            "name": "Alice Smith",
            "conflicts": {
                "travel": "Conflict: Alice is traveling to NYC from 2026-04-10 to 2026-04-15. No study blocks available.",
                "learning": "No conflict: Alice has 10 hours/week available for learning.",
                "groceries": "Conflict: Monday evening grocery block is fully booked.",
                "other": "No conflict: Standard flexible slot."
            }
        },
        "bob@company.com": {
            "name": "Bob Jones",
            "conflicts": {
                "learning": "Conflict: Bob has exams. No learning blocks available.",
                "health": "No conflict: Daily workout slot is clear.",
                "other": "No conflicts."
            }
        },
        "charlie@company.com": {
            "name": "Charlie Brown",
            "conflicts": {
                "other": "No conflicts."
            }
        },
        "security_test@company.com": {
            "name": "Security Test User",
            "conflicts": {
                "other": "No conflicts."
            }
        }
    }

    info = database.get(member_email.lower())
    if not info:
        return f"User {member_email} not found in the LifeOS schedule database."
    
    cat = category.lower().strip()
    conflicts = info.get("conflicts", {})
    conflict_desc = conflicts.get(cat, conflicts.get("other", "No conflicts detected."))
    
    return (
        f"User: {info['name']}\n"
        f"Category: {cat}\n"
        f"Schedule status: {conflict_desc}"
    )


@mcp.tool()
def validate_habit_coach_method(payment_desc: str) -> str:
    """Validate if the specified habit routines are approved and consistent.

    Args:
        payment_desc: The description of the habit routine (e.g., 'Daily study 30m', 'Gym workout').
    """
    desc_upper = payment_desc.upper()
    
    # Check for approved habits/routines
    if "VISA" in desc_upper or "4111" in desc_upper or "[CREDIT_CARD_REDACTED]" in desc_upper or "STUDY" in desc_upper:
        return "Habit verified: APPROVED study habit routine."
    elif "MASTERCARD" in desc_upper or "5555" in desc_upper or "GYM" in desc_upper:
        return "Habit verified: APPROVED fitness habit routine."
    elif "BANK TRANSFER" in desc_upper or "CHASE" in desc_upper or "MEDITATION" in desc_upper:
        return "Habit verified: APPROVED mindfulness routine."
    
    return f"Habit routine '{payment_desc}' is UNRECOGNIZED or inconsistent. Warning: Possible habit disruption risk!"


@mcp.tool()
def convert_timeframe_to_hours(amount: float, currency_code: str) -> str:
    """Converts a timeframe duration (e.g. 5 days, 2 weeks) to estimated total hours.

    Args:
        amount: The numeric quantity of the timeframe.
        currency_code: The unit (e.g., EUR for Days, GBP for Weeks, CAD for Months, USD for Hours).
    """
    units = {
        "EUR": 1.10,  # Days to hours factor (e.g. 1.1h prep per day)
        "GBP": 1.25,  # Weeks to hours factor
        "CAD": 0.73,  # Months to hours factor
        "INR": 0.012, # Minutes to hours factor
        "USD": 1.0,   # Hours
    }
    factor = units.get(currency_code.upper())
    if not factor:
        return f"Timeframe unit {currency_code} not supported."
    converted = amount * factor
    return f"{amount} {currency_code.upper()} converted to {converted:.2f} total estimated study/prep hours."


if __name__ == "__main__":
    mcp.run()
