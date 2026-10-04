#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 备用上传工具：通过 REST API 提交文件，不依赖 git push（适合 github.com 被墙/代理不通时）。

用法：
    export GH_TOKEN="ghp_xxx"                # 需要 repo 权限的 classic token
    python3 upload_to_github.py              # 上传全部文件（内容未变的自动跳过）
    python3 upload_to_github.py README.md    # 只上传指定文件
    python3 upload_to_github.py -m "feat: xxx" README.md  # 自定义 commit message
"""
import argparse
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
    ".github/workflows/eval.yml",
    "README.md",
    "tools/upload_to_github.py",
    "01-llm-eval-harness/README.md",
    "01-llm-eval-harness/eval_cases.json",
    "01-llm-eval-harness/eval_runner.py",
    "01-llm-eval-harness/report.md",
    "01-llm-eval-harness/docs/评测方案设计.md",
]


def gh_request(method, url, payload=None):
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


def upload(rel: str, message: str) -> str:
    """上传单个文件，返回 "ok" / "skip"。"""
    path = os.path.join(ROOT, rel)
    with open(path, "rb") as f:
        raw = f.read()
    local_sha = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()

    remote = gh_request("GET", f"{API}/contents/{urllib.parse.quote(rel)}")
    if remote and remote.get("sha") == local_sha:
        print(f"  跳过（内容未变）{rel}")
        return "skip"

    payload = {"message": message, "content": base64.b64encode(raw).decode()}
    if remote:
        payload["sha"] = remote["sha"]

    res = gh_request("PUT", f"{API}/contents/{urllib.parse.quote(rel)}", payload)
    print(f"  OK {rel} (commit {res['commit']['sha'][:8]})")
    return "ok"


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub API 备用上传工具")
    parser.add_argument("-m", "--message", default="chore: sync via API uploader", help="commit message")
    parser.add_argument("files", nargs="*", help="要上传的文件（相对仓库根目录），缺省为全部")
    args = parser.parse_args()

    if not TOKEN:
        sys.exit("请先 export GH_TOKEN=<你的 GitHub classic token，需 repo 权限>")
    files = args.files if args.files else ALL_FILES

    # 单个文件失败不能中断整批，否则前面的 OK 会混在报错里看不出来，
    # 造成「以为全都传上去了、实际只传了一半」（2026-10-04 真实踩过一次）。
    ok, skipped, failed = [], [], []
    for rel in files:
        try:
            (ok if upload(rel, args.message) == "ok" else skipped).append(rel)
        except SystemExit as e:
            failed.append((rel, str(e)))
            print(f"  ❌ {rel} 失败：{e}")
        except Exception as e:  # noqa: BLE001
            failed.append((rel, repr(e)))
            print(f"  ❌ {rel} 失败：{e}")

    print(f"\n已上传 {len(ok)} / 跳过 {len(skipped)} / 失败 {len(failed)}")
    if failed:
        print("失败清单（重跑本命令即可，已成功的会显示'跳过'）：")
        for rel, why in failed:
            print(f"  - {rel}  {why}")
        sys.exit(1)
    print(f"同步完成：https://github.com/{REPO}")


if __name__ == "__main__":
    main()
