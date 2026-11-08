#!/usr/bin/env python3
"""未 fill の .dwt を oracle に通す。止まったファイルは hang.txt に記録して外す。"""
import subprocess, sys, os, glob, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.dirname(os.path.abspath(__file__))
ORACLE = os.path.join(ROOT, "tools/dw-oracle/dw-oracle")
root = sys.argv[1] if len(sys.argv) > 1 else f"{S}/stage"
hang = set(open(f"{S}/hang.txt").read().split()) if os.path.exists(f"{S}/hang.txt") else set()

def unfilled():
    out = []
    for f in sorted(glob.glob(f"{root}/**/*.dwt", recursive=True)):
        if f in hang: continue
        if not re.search(r"^%%% (output|error)", open(f).read(), re.M):
            out.append(f)
    return out

while True:
    todo = unfilled()
    if not todo: break
    try:
        subprocess.run([ORACLE, "fill"] + todo, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        subprocess.run(["pkill", "-f", "DwOracle"])
        left = unfilled()
        stuck = left[0]
        print("hang:", stuck, flush=True)
        hang.add(stuck)
        open(f"{S}/hang.txt", "a").write(stuck + "\n")
print("done; hang:", len(hang))
