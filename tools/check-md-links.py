#!/usr/bin/env python3
"""Markdown の内部リンク（ファイルとアンカー）が有効か検査する。外部 URL は見ない。"""
import os
import re
import subprocess
import sys


def slug(heading):
    h = re.sub(r"[`*]", "", heading.strip().lower())
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def anchors(path):
    found, fence = set(), False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("```"):
                fence = not fence
            elif not fence:
                m = re.match(r"#{1,6}\s+(.*)", line)
                if m:
                    found.add(slug(m.group(1)))
    return found


def main():
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    os.chdir(root)
    files = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "*.md"], text=True).split()
    files = [f for f in files if os.path.exists(f)]
    cache, bad = {}, 0
    for f in files:
        text = re.sub(r"```.*?```", "", open(f, encoding="utf-8").read(), flags=re.S)
        for m in re.finditer(r'(?:\]\(|src=")([^)"#\s]*)(#[^)"\s]*)?', text):
            target, anchor = m.group(1), m.group(2)
            if re.match(r"(https?:|mailto:)", target):
                continue
            path = os.path.normpath(os.path.join(os.path.dirname(f), target)) if target else f
            if not os.path.exists(path):
                print(f"{f}: リンク先がない: {target}")
                bad += 1
            elif anchor and path.endswith(".md"):
                if path not in cache:
                    cache[path] = anchors(path)
                if anchor[1:] not in cache[path]:
                    print(f"{f}: アンカーがない: {target}{anchor}")
                    bad += 1
    print(f"{len(files)} 個の Markdown を検査: 問題 {bad} 件")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
