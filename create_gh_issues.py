import subprocess
import time
import re
import os

def run_command(cmd):
    try:
        # Force UTF-8 encoding for subprocess output to handle GitHub CLI emojis/text
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}")
        return None

def get_tasks_from_md(filename="task.md"):
    tasks = []
    current_phase = ""
    
    if not os.path.exists(filename):
        print(f"{filename} not found.")
        return []

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_phase = line.replace("## ", "").strip()
            elif line.startswith("- ["):
                # Parse checkbox
                # Format: - [x] Description <!-- id: ... -->
                match = re.match(r'- \[(.| )\] (.*?) (<!--.*-->)?', line)
                if match:
                    body_text = match.group(2).strip()
                    # Clean up HTML comments if any inside the text (though regex handles end)
                    body_text = re.sub(r'<!--.*?-->', '', body_text).strip()
                    
                    title = f"[{current_phase}] {body_text}"
                    body = f"**Task**: {body_text}\n\n**Phase**: {current_phase}\n\nGenerated from {filename}"
                    tasks.append({"title": title, "body": body})
    return tasks

def close_all_issues():
    print("Fetching open issues...")
    # List all open issues
    cmd = ["gh", "issue", "list", "--state", "open", "--limit", "1000", "--json", "number"]
    output = run_command(cmd)
    if not output:
        return

    import json
    try:
        issues = json.loads(output)
    except:
        print("Failed to parse issues json")
        return

    if not issues:
        print("No open issues to close.")
        return

    print(f"Closing {len(issues)} open issues...")
    for iss in issues:
        num = str(iss['number'])
        run_command(["gh", "issue", "close", num])
        print(f"Closed issue #{num}")
        time.sleep(0.5)

def create_issues(tasks):
    print(f"Creating {len(tasks)} new issues...")
    for i, task in enumerate(tasks):
        cmd = [
            "gh", "issue", "create",
            "--title", task["title"],
            "--body", task["body"]
        ]
        res = run_command(cmd)
        if res:
            print(f"[{i+1}/{len(tasks)}] Created: {res}")
        time.sleep(1)

if __name__ == "__main__":
    print("--- Resetting GitHub Issues ---")
    
    # 1. Close existing issues (Reset)
    close_all_issues()
    
    # 2. Parse task.md
    tasks = get_tasks_from_md()
    
    # 3. Create new issues
    if tasks:
        create_issues(tasks)
    else:
        print("No tasks found in task.md")
    
    print("--- Done ---")
