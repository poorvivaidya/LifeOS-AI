import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv()

def grade():
    # Load traces
    traces_path = Path("artifacts/traces/generated_traces.json")
    with open(traces_path, "r", encoding="utf-8") as f:
        traces_data = json.load(f)
    
    # Load config
    config_path = Path("tests/eval/eval_config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
        
    metrics_to_run = config_data.get("metrics_to_run", [])
    custom_metrics = {m["name"]: m for m in config_data.get("custom_metrics", [])}
    
    # Initialize GenAI Client using standard API key from environment
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    results = []
    
    summary = {}
    for metric_name in metrics_to_run:
        summary[metric_name] = {
            "num_cases_total": 0,
            "num_cases_valid": 0,
            "num_cases_error": 0,
            "scores": []
        }
        
    eval_cases = traces_data.get("eval_cases", [])
    
    for case in eval_cases:
        case_id = case.get("eval_case_id")
        prompt_content = case.get("prompt", {}).get("parts", [{}])[0].get("text", "")
        # Get final response
        responses = case.get("responses", [])
        response_content = ""
        if responses:
            response_content = responses[0].get("response", {}).get("parts", [{}])[0].get("text", "")
        
        # Serialize the agent data trace for the judge
        agent_data = json.dumps(case.get("agent_data", {}), indent=2)
        
        case_results = {
            "eval_case_id": case_id,
            "metrics": {}
        }
        
        for metric_name in metrics_to_run:
            summary[metric_name]["num_cases_total"] += 1
            metric = custom_metrics.get(metric_name)
            if not metric:
                print(f"Metric {metric_name} not found in custom_metrics")
                summary[metric_name]["num_cases_error"] += 1
                continue
                
            prompt_template = metric.get("prompt_template", "")
            
            # Format the template
            formatted_prompt = (
                prompt_template
                .replace("{prompt}", prompt_content)
                .replace("{response}", response_content)
                .replace("{agent_data}", agent_data)
            )
            
            print(f"Grading case '{case_id}' for metric '{metric_name}'...")
            
            try:
                # Call Gemini
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=formatted_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0
                    )
                )
                
                # Parse JSON response
                res_json = json.loads(response.text.strip())
                score = int(res_json.get("score"))
                explanation = res_json.get("explanation", "")
                
                case_results["metrics"][metric_name] = {
                    "score": score,
                    "explanation": explanation
                }
                summary[metric_name]["num_cases_valid"] += 1
                summary[metric_name]["scores"].append(score)
                print(f"  Score: {score} | Explanation: {explanation}")
            except Exception as e:
                print(f"  Error grading case '{case_id}' for metric '{metric_name}': {e}")
                case_results["metrics"][metric_name] = {
                    "error": str(e)
                }
                summary[metric_name]["num_cases_error"] += 1
                
        results.append(case_results)
        
    # Print Summary Table
    print("\n" + "="*50)
    print("                Evaluation Summary                ")
    print("="*50)
    print(f"{'Metric Name':<25} | {'Total':<6} | {'Valid':<6} | {'Error':<6} | {'Avg Score':<10}")
    print("-"*60)
    for m_name, info in summary.items():
        avg_score = sum(info["scores"]) / len(info["scores"]) if info["scores"] else 0.0
        print(f"{m_name:<25} | {info['num_cases_total']:<6} | {info['num_cases_valid']:<6} | {info['num_cases_error']:<6} | {avg_score:<10.2f}")
    print("="*50 + "\n")
    
    # Save the output results matching the format of agents-cli eval grade
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("artifacts/grade_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_json_path = output_dir / f"results_{timestamp}.json"
    full_report = {
        "summary": {
            m_name: {
                "num_cases_total": info["num_cases_total"],
                "num_cases_valid": info["num_cases_valid"],
                "num_cases_error": info["num_cases_error"],
                "mean_score": sum(info["scores"]) / len(info["scores"]) if info["scores"] else 0.0
            } for m_name, info in summary.items()
        },
        "results": results
    }
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
        
    print(f"Saved full results to {output_json_path}")
    
    # Also save as latest results.json so we can easily parse/read it
    latest_json_path = output_dir / "latest_results.json"
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

if __name__ == "__main__":
    grade()
