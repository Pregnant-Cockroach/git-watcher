import subprocess
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("MODEL")
LINES_LIMIT = 400


def run_git(args, repo_path):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result
    except Exception as e:
        print(f"❌ OS Error: {e}")
        return None


def update_repo(repo_path, branch_name):
    try:
        print(f"🔄 Switching on {branch_name} into {repo_path}...")
        run_git(["fetch", "origin"], repo_path)
        run_git(["checkout", branch_name], repo_path)
        run_git(["reset", "--hard", f"origin/{branch_name}"], repo_path)
        print(f"✅ Successfully switched on {branch_name}.")
        return True
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False


def get_last_commit_diff(repo_path):
    # 1. Statistics
    try:
        res_stat = run_git(["diff", "HEAD~1", "HEAD", "--shortstat"], repo_path)
        if res_stat and res_stat.stdout:
            print(f"📊 Git Stat: {res_stat.stdout.strip()}")
    except:
        pass

    # 2. DIFF request
    print("🔍 Requesting code...")
    
    # Files to skip
    excludes = [
        ":(exclude)*Test.java",      # Tests
        ":(exclude)**/target/*",     # Build
        ":(exclude)**/build/*",
        ":(exclude)*.lock",
        ":(exclude)*.sql",           # Dumps
        ":(exclude)*.md",            # Docs
        ":(exclude)*.txt",
        ":(exclude)*.xml",           # Configs
        ":(exclude)*.json",
        ":(exclude)*.properties",    # Settings
        ":(exclude)*.svg",
        ":(exclude)*.png",
        ":(exclude)*.jpg"
    ]

    # What to scan
    includes = [
        "*.java", "*.py", "*.js", "*.ts", "*.cpp", "*.h", "*.cs", "*.php", "*.html", "*.css"
    ]

    cmd = ["diff", "HEAD~1", "HEAD", "--unified=0", "--"] + includes + excludes

    result = run_git(cmd, repo_path)

    if not result or result.returncode != 0:
        print("❌ Couldn't get diff.")
        return None

    diff = result.stdout.strip()

    if not diff:
        print("ℹ️ Diff empty (no changes).")
        return None

    # 3. Limits
    MAX_CHARS = 30000
    if len(diff) > MAX_CHARS:
        print(f"✂️ Diff is too big ({len(diff)}). Cropping to {MAX_CHARS}...")
        return diff[:MAX_CHARS] + "\n...[CROPPED]..."

    return diff

def filter_diff_lines(raw_diff):
    """
    Cleans lines that were removed (-),
    So ai won't scan old code.
    Keeps only new changes (+).
    """
    lines = raw_diff.split('\n')
    clean_lines = []
    
    for line in lines:
        if line.startswith("diff --git") or line.startswith("index ") or line.startswith("@@") or line.startswith("+++"):
            clean_lines.append(line)
            continue

        if line.startswith("---"):
            continue

        if line.startswith("-"):
            continue

        clean_lines.append(line)
        
    return "\n".join(clean_lines)

def analyze_code(diff_text):
    if diff_text == "SKIP_MERGE":
        return "It's a Merge Request."
    if diff_text == "SKIP_TOO_LARGE":
        return f"Commit is too big."
    if not diff_text or len(diff_text) < 10:
        return "No changes found."

    clean_diff = filter_diff_lines(diff_text)

    if len(clean_diff) < 20: 
        return "✅ AI: nothing new was found."
        
    # === ANALYZE ===
    buffer_size = 4000
    cursor = 0
    final_verdict = ""

    print(f"Starting AI analyze ({len(clean_diff)} symbols)...")

    while cursor < len(clean_diff):
        chunk = clean_diff[cursor: cursor + buffer_size]
        
        prompt = (
                    "Role: Professional code reviewer.\n"
                    "Task: Analyze this git diff for issues: code smells, anti patterns, dead code, bad naming, unsafe constructs, leaked passwords.\n"
                    "Rules:\n"
                    "1. If no issues found, output EXACTLY one word: PASS\n"
                    "2. No conversational filler, no introductions.\n"
                    "3. Group issues by Class name.\n"
                    "\n"
                    "STRICT RESPONSE FORMAT EXAMPLE:\n"
                    "UserService.java:\n"
                    "- Hardcoded password on line 12\n"
                    "- Empty catch block in login method\n"
                    "\n"
                    "DatabaseConfig.java:\n"
                    "- Raw SQL usage poses injection risk\n"
                    "\n"
                    "CODE DIFF TO ANALYZE:\n"
                    f"{chunk}"
                )

        try:
            resp = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False, "options":{"num_thread":3}})
            if resp.status_code == 200:
                answer = resp.json().get('response', '').strip()
                if answer and "PASS" not in answer: # Skipping PASS replies
                     final_verdict += f"\n--- CHUNK ---\n{answer}\n"
        except Exception as e:
            final_verdict += f"\nError: {e}"

        cursor += buffer_size

    if not final_verdict.strip():
        return "AI didn't found any problem."
        
    return final_verdict