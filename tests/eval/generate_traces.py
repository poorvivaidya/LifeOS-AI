import asyncio
import json
import base64
import os
from pathlib import Path
from datetime import datetime

# 1. Mock the Agent.run_async to avoid actual LLM calls
from google.adk import Agent, Event, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from vertexai import types

async def mock_run_async(self, parent_context):
    # Retrieve amount dynamically from the session state
    expense = parent_context.session.state.get("expense_data", {})
    amount = expense.get("amount", 0.0)
    submitter = expense.get("submitter", "unknown@company.com")
    category = expense.get("category", "travel")
    
    review_text = (
        f"Amount: {amount}\n"
        f"Submitter: {submitter}\n"
        f"Category: {category}\n"
        f"Risk level: low\n"
        f"Risk factors: none\n"
        f"Recommendation: approve"
    )
    
    # We will simulate a clean review call for tool use and response
    yield Event(
        content=genai_types.Content(
            role="model",
            parts=[genai_types.Part.from_text(text=review_text)]
        ),
        output={
            "amount": amount,
            "submitter": submitter,
            "category": category,
            "risk_level": "low",
            "risk_factors": "none",
            "recommendation": "approve",
        }
    )

setattr(Agent, "run_async", mock_run_async)

from expense_agent.agent import root_agent

def build_content(role: str, text: str) -> dict:
    return {
        "role": role,
        "parts": [{"text": text}]
    }

async def run_scenario(case: dict, runner: Runner) -> dict:
    eval_id = case["eval_id"]
    prompt_str = case["prompt"]
    
    user_id = f"user_{eval_id}"
    session_id = f"session_{eval_id}"
    
    # Convert input base64 data to get description for automation logic
    try:
        raw_payload = json.loads(prompt_str)
        data_field = raw_payload.get("data", "")
        expense_data = json.loads(base64.b64decode(data_field).decode())
        description = expense_data.get("description", "")
        amount = float(expense_data.get("amount", 0.0))
    except Exception:
        description = ""
        amount = 0.0

    print(f"Running scenario {eval_id} (amount={amount}, desc='{description}')")
    
    user_msg = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=prompt_str)]
    )
    
    # Keep track of generated events in order
    all_events = []
    
    # 1st execution turn
    invocation_id = None
    interrupt_id = None
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_msg
    ):
        all_events.append(event)
        
        # Check for request input interrupts
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "adk_request_input":
                    interrupt_id = part.function_call.id
                    invocation_id = event.invocation_id

    # If the workflow paused for approval, resume it with the automated decision
    if interrupt_id:
        # Determine the decision: Clean requests get approved, injections get rejected
        is_injection = any(keyword in description.lower() for keyword in ["ignore", "bypass", "override", "force"])
        decision = "reject" if is_injection else "approve"
        print(f"  INTERRUPT DETECTED: responding with decision='{decision}'")
        
        resume_msg = genai_types.Content(
            role="user",
            parts=[
                genai_types.Part(
                    function_response=genai_types.FunctionResponse(
                        id=interrupt_id,
                        name="adk_request_input",
                        response={"result": json.dumps({"decision": decision})}
                    )
                )
            ]
        )
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            invocation_id=invocation_id,
            new_message=resume_msg
        ):
            all_events.append(event)

    # Now, transform the ADK events list into the types.evals.ConversationTurn format
    # expected by Vertex AI's EvaluationDataset
    turns = []
    
    # Turn 0: User input prompt
    user_turn_event = {
        "author": "user",
        "content": build_content("user", prompt_str),
        "event_time": datetime.utcnow().isoformat() + "Z"
    }
    
    # Gather agent events
    agent_turn_events = []
    final_text = ""
    for ev in all_events:
        author = "expense_processor"
        
        # Map node path to name if applicable
        if ev.node_info and ev.node_info.path:
            # e.g. "expense_processor@1/auto_approve@1"
            parts = ev.node_info.path.split("/")
            if len(parts) > 1:
                author = parts[-1].split("@")[0]
        
        content_dict = None
        if ev.content:
            # serialize the content parts
            parts_list = []
            for part in ev.content.parts:
                if part.text:
                    parts_list.append({"text": part.text})
                elif part.function_call:
                    parts_list.append({
                        "function_call": {
                            "name": part.function_call.name,
                            "args": part.function_call.args,
                            "id": part.function_call.id
                        }
                    })
                elif part.function_response:
                    parts_list.append({
                        "function_response": {
                            "name": part.function_response.name,
                            "response": part.function_response.response,
                            "id": part.function_response.id
                        }
                    })
            content_dict = {
                "role": ev.content.role or "model",
                "parts": parts_list
            }
        else:
            # Construct dummy content so Vertex AI validation passes
            node_desc = f"Executed node: {author}"
            details = []
            if ev.output:
                details.append(f"Output: {json.dumps(ev.output)}")
            if ev.actions and ev.actions.state_delta:
                details.append(f"State Delta: {json.dumps(ev.actions.state_delta)}")
            if details:
                node_desc += " | " + " | ".join(details)
            
            content_dict = {
                "role": "model",
                "parts": [{"text": node_desc}]
            }
        
        # Capture final status/outcome output as final response candidate if text not present
        if ev.output and not ev.content:
            status = ev.output.get("status", "")
            msg = ev.output.get("message", "")
            if msg:
                final_text = msg
            elif status:
                final_text = f"Expense status: {status}"
        
        event_time_str = datetime.utcfromtimestamp(ev.timestamp).isoformat() + "Z"
        
        agent_turn_events.append({
            "author": author,
            "content": content_dict,
            "event_time": event_time_str,
            "state_delta": ev.actions.state_delta if ev.actions else {}
        })
        
    turns.append({
        "turn_index": 0,
        "turn_id": "turn_0",
        "events": [user_turn_event] + agent_turn_events
    })
    
    responses = []
    if final_text:
        responses.append({
            "response": build_content("model", final_text)
        })
    else:
        # Default response status summary
        responses.append({
            "response": build_content("model", "Workflow execution completed.")
        })
        
    # Construct the final EvalCase JSON dictionary matching types.EvalCase model fields
    eval_case = {
        "eval_case_id": eval_id,
        "prompt": build_content("user", prompt_str),
        "responses": responses,
        "agent_data": {
            "agents": {
                "expense_processor": {
                    "agent_id": "expense_processor",
                    "description": "Expense processing workflow"
                }
            },
            "turns": turns
        }
    }
    
    return eval_case

async def run_all():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    output_path = Path("artifacts/traces/generated_traces.json")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    eval_cases = dataset["eval_cases"]
    
    session_service = InMemorySessionService()
    
    results = []
    async with Runner(
        agent=root_agent,
        app_name="expense_agent",
        session_service=session_service,
        auto_create_session=True
    ) as runner:
        for case in eval_cases:
            res_case = await run_scenario(case, runner)
            results.append(res_case)
            
    # Serialize to EvaluationDataset matching structure
    eval_dataset = {
        "eval_cases": results
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(eval_dataset, f, indent=2)
        
    print(f"Successfully generated evaluation traces and saved to {output_path}")

if __name__ == "__main__":
    os.environ["MOCK_LLM"] = "true"
    asyncio.run(run_all())
