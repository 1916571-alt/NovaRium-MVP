import os
import subprocess
import sys


def main() -> int:
    env = os.environ.copy()
    if env.get("RUN_DB_INTEGRATION") != "1":
        env["RUN_DB_INTEGRATION"] = "1"

    if not env.get("DATABASE_URL"):
        print("DATABASE_URL is required for smoke flow.")
        return 1

    commands = [
        [sys.executable, "scripts/apply_migrations.py"],
        ["pytest", "-q", "tests/test_rls_integration.py"],
        ["pytest", "-q", "tests/test_e2e_flow_integration.py"],
    ]

    for cmd in commands:
        print(f"$ {' '.join(cmd)}")
        completed = subprocess.run(cmd, env=env, cwd=os.path.dirname(os.path.dirname(__file__)))
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
