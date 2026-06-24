import urllib.request
import json
import concurrent.futures
import time

BACKEND_URL = "http://localhost:8080"

def get_sessions():
    url = f"{BACKEND_URL}/apps/expense_agent/users/test-sub/sessions"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())

def get_full_session(session_id):
    url = f"{BACKEND_URL}/apps/expense_agent/users/test-sub/sessions/{session_id}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())

def main():
    print("Fetching sessions list...")
    t0 = time.time()
    sessions = get_sessions()
    t1 = time.time()
    print(f"Fetched {len(sessions)} sessions in {t1 - t0:.3f} seconds.")
    
    if not sessions:
        return
        
    print("\nKeys of a session from list:")
    print(list(sessions[0].keys()))
    print("Example state:", sessions[0].get("state"))
    
    print("\nFetching full sessions sequentially (first 10)...")
    t0 = time.time()
    for s in sessions[:10]:
        get_full_session(s["id"])
    t1 = time.time()
    print(f"Fetched 10 sessions sequentially in {t1 - t0:.3f} seconds.")
    
    print("\nFetching full sessions concurrently using ThreadPoolExecutor (all of them)...")
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(lambda s: get_full_session(s["id"]), sessions))
    t1 = time.time()
    print(f"Fetched all {len(sessions)} sessions concurrently in {t1 - t0:.3f} seconds.")

if __name__ == "__main__":
    main()
