#!/usr/bin/env python3
"""
Kimi Chat Exporter
==================
Export all Kimi (kimi.com) conversation history to Markdown files.

How to get your token:
  1. Open https://www.kimi.com and log in
  2. Press F12 → Console tab
  3. Run: copy(localStorage.getItem('access_token') || localStorage.getItem('refresh_token'))
  4. Your token is now in the clipboard

Usage:
  python kimi_exporter.py --token "YOUR_TOKEN_HERE"
  python kimi_exporter.py --token "YOUR_TOKEN_HERE" --output ./my_kimi_exports
  python kimi_exporter.py --token "YOUR_TOKEN_HERE" --delay 0.8
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# Windows terminal UTF-8 compatibility
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)

BASE_URL = "https://www.kimi.com"
PAGE_SIZE = 50


# ──────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────

def http_post(path: str, body: dict, token: str) -> dict:
    url = BASE_URL + path
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Origin": BASE_URL,
        "Referer": BASE_URL + "/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} on {path}: {body_text[:300]}")


# ──────────────────────────────────────────────
# Fetch conversation list
# ──────────────────────────────────────────────

def fetch_all_chats(token: str) -> list:
    chats = []
    offset = 0
    print("Fetching conversation list...", flush=True)
    while True:
        resp = http_post(
            "/apiv2/kimi.chat.v1.ChatService/ListChats",
            {"offset": offset, "limit": PAGE_SIZE},
            token,
        )
        items = (
            resp.get("chats")
            or resp.get("items")
            or resp.get("data", {}).get("chats")
            or []
        )
        if not items:
            break
        chats.extend(items)
        print(f"  Fetched {len(chats)} conversations...", end="\r", flush=True)
        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.3)
    print(f"Found {len(chats)} conversations.{'':30}")
    return chats


# ──────────────────────────────────────────────
# Fetch messages for a single conversation
# ──────────────────────────────────────────────

def fetch_messages(chat_id: str, token: str) -> list:
    paths = [
        ("/apiv2/kimi.chat.v1.ChatService/ListMessages", {"chat_id": chat_id, "limit": 500}),
        ("/apiv1/chat/list", {"id": chat_id}),
    ]
    for path, body in paths:
        try:
            resp = http_post(path, body, token)
            msgs = (
                resp.get("messages")
                or resp.get("items")
                or resp.get("data", {}).get("messages")
                or []
            )
            if msgs:
                return msgs
        except Exception:
            continue
    return []


# ──────────────────────────────────────────────
# Markdown generation
# ──────────────────────────────────────────────

def extract_text(content) -> str:
    """Recursively extract plain text from various content structures."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [extract_text(item) for item in content]
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict):
        for key in ("text", "value", "content", "body"):
            if key in content and content[key]:
                return extract_text(content[key])
        parts = [extract_text(v) for v in content.values() if v]
        return "\n".join(p for p in parts if p)
    return ""


def to_markdown(title: str, messages: list, chat_id: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"> **Exported**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> **Chat ID**: `{chat_id}`",
        f"> **Messages**: {len(messages)}",
        "",
        "---",
        "",
    ]

    for msg in messages:
        role_raw = (
            msg.get("role") or msg.get("sender") or msg.get("type") or "unknown"
        ).lower()

        if "user" in role_raw or "human" in role_raw:
            role_icon, role_name = "👤", "User"
        elif "assistant" in role_raw or "kimi" in role_raw or "ai" in role_raw:
            role_icon, role_name = "🤖", "Kimi"
        else:
            role_icon, role_name = "💬", role_raw.capitalize()

        content = extract_text(
            msg.get("content") or msg.get("text") or msg.get("message") or ""
        )
        if not content:
            continue

        lines += [f"### {role_icon} {role_name}", "", content, "", "---", ""]

    return "\n".join(lines)


def safe_filename(title: str, index: int) -> str:
    title = title.strip() or "Untitled"
    title = re.sub(r'[\\/:*?"<>|\r\n]', "_", title)
    title = title[:80]
    return f"{index:04d}_{title}.md"


# ──────────────────────────────────────────────
# Main export flow
# ──────────────────────────────────────────────

def run(token: str, output_dir: str, delay: float):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {os.path.abspath(output_dir)}\n")

    try:
        chats = fetch_all_chats(token)
    except RuntimeError as e:
        if "401" in str(e) or "403" in str(e):
            print("\nError: Token is invalid or expired. Please get a new one.")
            print("  In the browser console at kimi.com, run:")
            print("  copy(localStorage.getItem('access_token') || localStorage.getItem('refresh_token'))")
        else:
            print(f"\nError fetching conversation list: {e}")
        sys.exit(1)

    if not chats:
        print("No conversations found. Make sure your token is correct.")
        sys.exit(0)

    success, failed = 0, []
    total = len(chats)

    for i, chat in enumerate(chats):
        chat_id = chat.get("id") or chat.get("chat_id") or ""
        title = (
            chat.get("title") or chat.get("name") or chat.get("subject") or f"Chat_{i+1}"
        )
        if not chat_id:
            continue

        print(f"  [{i+1:>{len(str(total))}}/{total}] {title[:60]}", end=" ", flush=True)

        try:
            messages = fetch_messages(chat_id, token)
            md = to_markdown(title, messages, chat_id)
            fname = safe_filename(title, i + 1)
            fpath = os.path.join(output_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"OK ({len(messages)} messages)")
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append({"id": chat_id, "title": title, "error": str(e)})

        time.sleep(delay)

    if failed:
        fail_path = os.path.join(output_dir, "_FAILED.json")
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"\nWarning: {len(failed)} conversations failed. See _FAILED.json for details.")

    print(f"\nDone! Exported {success}/{total} conversations.")
    print(f"Saved to: {os.path.abspath(output_dir)}")


def main():
    default_output = os.path.join(os.path.expanduser("~"), "Desktop", "kimi_exports")

    parser = argparse.ArgumentParser(
        description="Export all Kimi (kimi.com) conversation history to Markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--token", required=True, help="Your Kimi access_token or refresh_token")
    parser.add_argument("--output", default=default_output, help=f"Output directory (default: {default_output})")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    args = parser.parse_args()

    run(args.token, args.output, args.delay)


if __name__ == "__main__":
    main()
