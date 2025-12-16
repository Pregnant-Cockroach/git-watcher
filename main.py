import asyncio
import subprocess
import os
from fastapi import FastAPI
from datetime import datetime
from scanner import analyze_code, get_last_commit_diff, update_repo
from dotenv import load_dotenv

load_dotenv()

def save_report(text):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"logs/report_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

app = FastAPI()

# === CONFIG ===
CHECK_INTERVAL = 60
TARGET_REPO_PATH = os.getenv("TARGET_REPO_PATH")
BRANCH = os.getenv("WATCH_BRANCH", "main") # "main" - default value
if not TARGET_REPO_PATH:
    raise ValueError("❌ TARGET_REPO_PATH is not specified in .env file!")

@app.get("/health")
def health():
    return {"status": "watching", "target": TARGET_REPO_PATH}


async def git_watcher():
    print(f"🕵️ Watcher was started for {TARGET_REPO_PATH}")
    while True:
        try:
            # Fetch
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=TARGET_REPO_PATH,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Comparing hash
            local = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=TARGET_REPO_PATH, text=True).strip()
            remote = subprocess.check_output(["git", "rev-parse", f"origin/{BRANCH}"], cwd=TARGET_REPO_PATH,
                                             text=True).strip()

            if local != remote:
                print(f"\n🔔 Change detected! {local[:7]} -> {remote[:7]}")
                run_pipeline()

        except Exception as e:
            print(f"⚠️ Watcher error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


def run_pipeline():
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Start")
    if not update_repo(TARGET_REPO_PATH, BRANCH):
        return

    diff = get_last_commit_diff(TARGET_REPO_PATH)

    if not diff or diff.startswith("SKIP"):
        print(f"⏭️ Skip: {diff}")
        return

    report = analyze_code(diff)
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}🤖 REPORT:\n{report}")
    save_report(report)

@app.on_event("startup")
async def start():
    asyncio.create_task(git_watcher())
