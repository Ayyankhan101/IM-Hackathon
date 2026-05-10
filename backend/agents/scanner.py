import os
import shutil
import tempfile
import git

MAX_SIZE_MB = 50
MAX_FILES = 300
SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".zip", ".tar", ".gz", ".lock",
    ".min.js", ".min.css",
}
SKIP_DIRS = {"node_modules", ".git", "venv", "__pycache__", "dist", "build", ".next"}


def run_scanner(state: dict) -> dict:
    repo_url = state["repo_url"]
    tmp = tempfile.mkdtemp(prefix="gitmind_")

    try:
        git.Repo.clone_from(repo_url, tmp, depth=1)
    except Exception as e:
        return {"events": [{"type": "error", "agent": "scanner", "message": str(e)}]}

    file_tree = []
    file_contents = {}
    total_size = 0

    for root, dirs, files in os.walk(tmp):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if len(file_tree) >= MAX_FILES:
                break
            _, ext = os.path.splitext(fname)
            if ext.lower() in SKIP_EXTS:
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, tmp)
            size = os.path.getsize(fpath)
            total_size += size
            if total_size > MAX_SIZE_MB * 1024 * 1024:
                break
            file_tree.append(rel)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    file_contents[rel] = f.read()
            except Exception:
                file_contents[rel] = ""

    return {
        "local_path": tmp,
        "file_tree": file_tree,
        "file_contents": file_contents,
        "events": [{"type": "agent_done", "agent": "scanner", "message": f"Scanned {len(file_tree)} files"}],
    }
