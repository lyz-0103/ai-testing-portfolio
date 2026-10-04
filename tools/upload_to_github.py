#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 备用上传工具：通过 REST API 提交文件，不依赖 git push（适合 github.com 被墙/代理不通时）。

用法：
    export GH_TOKEN="ghp_xxx"                # 需要 repo 权限的 classic token
    python3 upload_to_github.py              # 上传全部文件（内容未变的自动跳过）
    python3 upload_to_github.py README.md    # 只上传指定文件

原理：GET /contents/{path} 对比 blob sha -> 内容有变化时 PUT 覆盖并生成 commit。
"""
import base64
import hashlib
import json
import os
import sys
import urllib.request
import urllib.parse

REPO = os.environ.get("GH_REPO", "lyz-0103/ai-testing-portfolio")
TOKEN = os.environ.get("GH_TOKEN", "")
API = f"https://api.github.com/repos/{REPO}"
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

ALL_FILES = [
    ".gitignore",
    "README.md",
    "GitHub上传教程.md",
    "01-llm-eval-harness/README.md",
    "01-llm-eval-harness/eval_cases.json",
    "01-llm-eval-harness/eval_runner.py",
    "01-llm-eval-harness/report.md",
]


def gh_request(method: str, url: str, payload: dict | None = None) -> dict | None:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "portfolio-uploader",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def upload(rel: str, message: str) -> None:
    path = os.path.join(ROOT, rel)
    with open(path, "rb") as f:
        raw = f.read()
    local_sha = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()

    remote = gh_request("GET", f"{API}/contents/{urllib.parse.quote(rel)}")
    if remote and remote.get("sha") == local_sha:
        print(f"  跳过（内容未变）{rel}")
        return

    payload = {"message": message, "content": base64.b64encode(raw).decode()}
    if remote:
        payload["sha"] = remote["sha"]

    res = gh_request("PUT", f"{API}/contents/{urllib.parse.quote(rel)}", payload)
    print(f"  OK {rel} (commit {res['commit']['sha'][:8]})")


def main() -> None:
    if not TOKEN:
        sys.exit("请先 export GH_TOKEN=<你的 GitHub classic token，需 repo 权限>")
    files = sys.argv[1:] if len(sys.argv) > 1 else ALL_FILES
    msg = "docs: update via API uploader"
    for rel in files:
        upload(rel, msg)
    print(f"\n同步完成：https://github.com/{REPO}")


if __name__ == "__main__":
    main()
