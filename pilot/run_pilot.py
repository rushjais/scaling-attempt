"""Run one pilot attempt at the Pelican os.path -> pathlib migration, then hand-check it.

    python3 run_pilot.py --label p1 --model claude-opus-5-5 [--timeout 120] [--budget 20]

Workspace: pilot/work/<id>/repo (inside the project, so a reboot can't wipe it),
a fresh git repo of Pelican at the pin with one commit, mounted alone into the
pilot Docker image. Output: pilot/runs/<id>/ with transcript, diff, and the
check.py summary.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DOCKER = shutil.which("docker") or "/Applications/Docker.app/Contents/Resources/bin/docker"
IMAGE = "pelican-migration-pilot"
TOKEN_FILE = os.path.expanduser("~/.config/snapshot-task/oauth_token")
ALLOWED = "Bash Read Edit Write Glob Grep TodoWrite"
DENIED = "WebFetch WebSearch"
HARNESS_NOTE = ("You are running non-interactively: when you end your turn, the session ends "
                "and nothing you started in the background will report back. Run commands in "
                "the foreground, and finish the task before ending your turn.")


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--timeout", type=float, default=120, help="minutes")
    ap.add_argument("--budget", type=float, default=20.0)
    args = ap.parse_args()

    token = open(TOKEN_FILE).read().strip()
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + args.label
    work = os.path.join(HERE, "work", run_id)
    out = os.path.join(HERE, "runs", run_id)
    os.makedirs(out)
    repo = os.path.join(work, "repo")
    shutil.copytree(os.path.join(HERE, "upstream"), repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    env_git = {**os.environ, "GIT_AUTHOR_NAME": "dev", "GIT_AUTHOR_EMAIL": "dev@example.com",
               "GIT_COMMITTER_NAME": "dev", "GIT_COMMITTER_EMAIL": "dev@example.com"}
    sh(["git", "init", "-q"], cwd=repo)
    sh(["git", "add", "-A"], cwd=repo)
    sh(["git", "commit", "-q", "-m", "pelican at pin"], cwd=repo, env=env_git)

    if sys.platform == "darwin" and shutil.which("caffeinate"):
        subprocess.Popen(["caffeinate", "-ims", "-w", str(os.getpid())])

    prompt = open(os.path.join(HERE, "PROMPT.md")).read()
    container = "pelican-pilot-" + run_id
    cmd = [DOCKER, "run", "--rm", "--name", container, "--user", f"{os.getuid()}:{os.getgid()}",
           "--memory", "4g", "--cpus", "2", "-e", "CLAUDE_CODE_OAUTH_TOKEN",
           "-v", f"{repo}:/work/repo", "-w", "/work/repo", IMAGE,
           "claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "dontAsk", "--allowedTools", ALLOWED, "--disallowedTools", DENIED,
           "--strict-mcp-config", "--setting-sources", "project", "--no-session-persistence",
           "--max-budget-usd", str(args.budget), "--append-system-prompt", HARNESS_NOTE,
           "--model", args.model]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") and k != "ANTHROPIC_BASE_URL"}
    env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    print(f"[{run_id}] workspace {repo}", flush=True)
    start, deadline = time.time(), time.time() + args.timeout * 60
    with open(os.path.join(out, "transcript.jsonl"), "w") as t, open(os.path.join(out, "stderr.txt"), "w") as e:
        proc = subprocess.Popen(cmd, env=env, stdout=t, stderr=e)
        while proc.poll() is None and time.time() < deadline:
            time.sleep(2)
        status = f"exit {proc.returncode}" if proc.poll() is not None else "timeout"
        if status == "timeout":
            subprocess.run([DOCKER, "kill", container], capture_output=True)
            proc.kill()
            proc.wait()
    minutes = round((time.time() - start) / 60, 1)
    print(f"[{run_id}] agent finished: {status} after {minutes} min", flush=True)

    diff = subprocess.run(["git", "diff", "HEAD", "--stat"], cwd=repo, capture_output=True, text=True).stdout
    full = subprocess.run(["git", "diff", "HEAD"], cwd=repo, capture_output=True, text=True).stdout
    open(os.path.join(out, "diff.stat"), "w").write(diff)
    open(os.path.join(out, "diff.patch"), "w").write(full)

    result = {}
    for line in open(os.path.join(out, "transcript.jsonl")):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result = ev
    check = subprocess.run([sys.executable, os.path.join(HERE, "check", "check.py"), repo],
                           capture_output=True, text=True)
    summary = {"run_id": run_id, "model": args.model, "status": status, "minutes": minutes,
               "cost_usd": result.get("total_cost_usd"), "agent_final_message": result.get("result"),
               "files_changed": diff.strip().splitlines()[-1] if diff.strip() else "none",
               "check": json.loads(check.stdout) if check.returncode == 0 else check.stderr[-2000:]}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in summary.items() if k != "agent_final_message"}, indent=2))


if __name__ == "__main__":
    main()
