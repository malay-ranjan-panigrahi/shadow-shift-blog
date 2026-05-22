import subprocess
import ollama
import sys
import json
import re
from collections import Counter

def get_k8s_logs(namespace, deployment_name):
    """Executes kubectl to fetch the last 30 log lines."""
    cmd = ["kubectl", "logs", f"deploy/{deployment_name}", "-n", namespace, "-c", "blog", "--tail=30"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching logs for {deployment_name}: {e}")
        sys.exit(1)

def parse_status_codes(log_text):
    """
    Bulletproof Regex: Looks for the closing quote of the HTTP request, 
    followed by a space, then exactly 3 digits.
    """
    if not log_text:
        return {}
    
    pattern = r'"\s+([1-5]\d{2})\s+'
    codes = re.findall(pattern, log_text)
    return dict(Counter(codes))

def run_ai_analysis():
    print("🔍 Fetching live Nginx logs from cluster...")
    v1_logs = get_k8s_logs("prod", "blog-prod")
    v2_logs = get_k8s_logs("shadow", "blog-shadow")

    print("⚙️  Pre-processing logs and extracting HTTP metrics...")
    v1_metrics = parse_status_codes(v1_logs)
    v2_metrics = parse_status_codes(v2_logs)
    
    print(f"   V1 Metrics: {v1_metrics}")
    print(f"   V2 Metrics: {v2_metrics}")

    if not v1_metrics or not v2_metrics:
        print("\n⚠️  ABORTING: No HTTP requests found in logs.")
        print("➡️  ACTION REQUIRED: Go to http://localhost:8888 and refresh the page 5 times, then run this script again.\n")
        return

    # ENTERPRISE SRE PATTERN: Python handles logic, AI handles communication
    has_errors = any(code.startswith('4') or code.startswith('5') for code in v2_metrics.keys())
    system_status = "FAIL" if has_errors else "PASS"

    # HARDENED PROMPT
    prompt = f"""
    You are an automated SRE alert generator.
    The deterministic system health check has resulted in a status of: {system_status}.
    
    V1 Status Codes (Stable): {v1_metrics}
    V2 Status Codes (Shadow): {v2_metrics}
    
    Write a brief, 1-sentence reason explaining why the system got a {system_status} status based on these metrics.
    Output strictly as JSON with exactly two keys: "decision" (must be exactly "{system_status}") and "reason".
    """

    print("🧠 Generating SRE incident report via Ollama...")
    
    try:
        response = ollama.chat(model='gemma:2b', messages=[
            {'role': 'user', 'content': prompt}
        ], format='json')
        
        ai_data = json.loads(response['message']['content'])
        
        print("\n================ AI SRE ANALYSIS ================")
        print(f"DECISION: [{ai_data.get('decision', 'ERROR')}]")
        print(f"REASON:   {ai_data.get('reason', 'No reasoning provided.')}")
        print("=================================================\n")
        
    except json.JSONDecodeError:
        print("❌ AI failed to return valid JSON.")
    except Exception as e:
        print(f"❌ Execution Error: {e}")

# This is the line that actually tells Python to run the code!
if __name__ == "__main__":
    run_ai_analysis()
