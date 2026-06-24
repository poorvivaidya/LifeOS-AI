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

import pytest
from google.adk import Agent, Event
from google.genai import types

@pytest.fixture(autouse=True)
def mock_agent_run(monkeypatch):
    """Mock Agent.run_async to avoid calling the real LLM APIs in tests."""

    async def mock_run_async(self, parent_context):
        # Yield a single Event containing both content (text parts) and structured output
        yield Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text="Reviewing high-value expense...")]
            ),
            output={
                "amount": 250.0,
                "submitter": "alice@company.com",
                "category": "travel",
                "risk_level": "low",
                "risk_factors": "none",
                "recommendation": "approve",
            }
        )

    monkeypatch.setattr(Agent, "run_async", mock_run_async)
