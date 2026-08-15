import sys, time, subprocess, json

run_id = sys.argv[1]
while True:
    try:
        out = subprocess.getoutput(f"gh run view {run_id} --json status,conclusion")
        data = json.loads(out)
        print(f"Current status: {data.get('status')}")
        if data.get("status") == "completed":
            print("RUN COMPLETED")
            print("Conclusion:", data.get("conclusion"))
            break
    except Exception as e:
        print(f"Error parsing json: {e}")
    time.sleep(30)

print(subprocess.getoutput(f"gh run view {run_id}"))
if data.get("conclusion") != "success":
    subprocess.getoutput(f"gh run view {run_id} --log-failed > failed_run_{run_id}.log")
    print(f"Saved failed logs to failed_run_{run_id}.log")
