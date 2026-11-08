#!/usr/bin/env python3
"""mulay.wasm の入口 (load・run・call・scaffold・components) を、ネイティブの ASan 版で壊した入力にかける。

  tools/fuzz/fuzz.py [-n 回数] [-j 並び (既定 4、4 コアまで)] [-t 秒] [--seed N] [--out DIR]

入口のバイナリは tools/fuzz/entry.clay を clay build --asan で組んだもの (無ければ組む。FUZZ_BIN で替えられる)。
種は test/fixtures/livenote の各アプリ (livenote/examples.json の例を run に渡す) と、DW の golden (test/fixtures/dw) を
ee:transform に入れた小さなアプリ。壊し方はバイトの変更・削除・重複・継ぎ合わせと、深い入れ子・巨大な数・壊れた UTF-8・
式や実体の差し込み。見つけたもの (ASan、clay の中断、時間切れ) は --out (既定 target/fuzz) に、入力のディレクトリと
出力を残す。同じ種類 (最初のエラー行) は 1 つだけ残す。
"""
import argparse, glob, json, os, random, re, shutil, subprocess, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT_EXT = (".xml", ".dwl", ".json", ".raml", ".yaml", ".yml", ".properties", ".csv", ".txt")

TOKENS = [b"[" * 3000, b"{" * 3000, b"(" * 3000, b"<a>" * 3000, b"9" * 400, b"1e999999", b"-0x7fffffffffffffff",
          b"\xff\xfe", b"\xc3", b"\xed\xa0\x80", b"\x00", b"${", b"${a}", b"#[", b"#[payload", b"]", b"%dw 2.0\n---\n",
          b"<!DOCTYPE a [<!ENTITY e \"&e;&e;\">]>", b"&e;", b"&#x110000;", b"<![CDATA[", b"]]>", b"../../../../etc/passwd",
          b"classpath://", b"\"", b"\\u", b"\\ud800", b"0 to 2147483647", b"fun f(x) = f(x)\n---\nf(1)", b"'" * 50,
          b"do {", b"else", b"match", b"case", b"as Number", b"as Date {format: \"yyyy\"}", b"(.+)+$", b"*" * 100, b"?", b"null",
          b"\t" * 50, b"\r\n" * 50, b"%", b"@", b"!", b"..", b"..."]


def build(bin_path):
    if os.path.exists(bin_path) and os.path.getmtime(bin_path) > newest_src():
        return
    os.makedirs(os.path.dirname(bin_path), exist_ok=True)
    r = subprocess.run(["taskset", "-c", "0-3", "clay", "build", "--asan", "entry.clay", "-o", bin_path], cwd=HERE,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        sys.exit(r.stdout[-3000:])


def newest_src():
    t = os.path.getmtime(os.path.join(HERE, "entry.clay"))
    for p in glob.glob(os.path.join(REPO, "src", "mulay", "**", "*.clay"), recursive=True):
        t = max(t, os.path.getmtime(p))
    return t


def read_tree(d):
    out = {}
    for p in glob.glob(os.path.join(d, "**", "*"), recursive=True):
        if os.path.isfile(p) and "/target/" not in p:
            out[os.path.relpath(p, d)] = open(p, "rb").read()
    return out


def seeds():
    ss = []
    for d in sorted(glob.glob(os.path.join(REPO, "test", "fixtures", "livenote", "*"))):
        files = read_tree(d)
        exs = []
        ej = files.get("livenote/examples.json")
        if ej:
            try:
                exs = [json.dumps(e).encode() for e in json.loads(ej)]
            except ValueError:
                pass
        ss.append((files, exs))
    dw = sorted(glob.glob(os.path.join(REPO, "test", "fixtures", "dw", "**", "*.dwt"), recursive=True))
    for p in dw[::37]:
        txt = open(p, "rb").read()
        m = re.search(rb"(?s)%%% script\n(.*?)\n%%%", txt) or re.search(rb"(?s)^(.*?)\n%%%", txt)
        script = m.group(1) if m else txt[:2000]
        ss.append(dw_app(script))
    return ss


def dw_app(script):
    xml = (b'<?xml version="1.0" encoding="UTF-8"?>\n<mule xmlns="http://www.mulesoft.org/schema/mule/core" '
           b'xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core" xmlns:http="http://www.mulesoft.org/schema/mule/http">\n'
           b'<http:listener-config name="L"><http:listener-connection host="0.0.0.0" port="8081"/></http:listener-config>\n'
           b'<flow name="f"><http:listener config-ref="L" path="/f"/><ee:transform><ee:message><ee:set-payload><![CDATA[' + script +
           b']]></ee:set-payload></ee:message></ee:transform></flow>\n</mule>\n')
    ex = json.dumps({"id": "x", "name": "x", "flow": "f", "request": {"method": "POST", "path": "/f", "mediaType": "application/json",
                                                                       "body": "{\"a\": [1, 2, {\"b\": \"c\"}], \"n\": 1.5}"}}).encode()
    return ({"src/main/mule/app.xml": xml, "mule-artifact.json": b'{"minMuleVersion": "4.6.0"}'}, [ex])


def mutate(rng, b, other):
    b = bytearray(b)
    for _ in range(rng.randint(1, 4)):
        k = rng.randrange(7)
        n = len(b)
        if k == 0 and n:
            i = rng.randrange(n); b[i] = rng.randrange(256)
        elif k == 1 and n:
            i = rng.randrange(n); j = min(n, i + rng.randint(1, 64)); del b[i:j]
        elif k == 2 and n:
            i = rng.randrange(n); j = min(n, i + rng.randint(1, 64)); b[i:i] = b[i:j] * rng.randint(2, 50)
        elif k == 3:
            i = rng.randrange(n + 1); b[i:i] = rng.choice(TOKENS)
        elif k == 4 and other:
            i = rng.randrange(n + 1); j = rng.randrange(len(other)); b[i:i] = other[j:j + rng.randint(1, 200)]
        elif k == 5 and n:
            i = rng.randrange(n); b = b[:i]
        elif k == 6 and n:
            i = rng.randrange(n); c = b[i:i + 1]; b[i:i + 1] = c * rng.randint(100, 5000)
    return bytes(b)


def case(rng, ss):
    files, exs = rng.choice(ss)
    files = dict(files)
    exs = list(exs) or [b'{"id":"x","name":"x","flow":"f","request":{"method":"GET","path":"/"}}']
    other = rng.choice(ss)[0]
    other_b = rng.choice(list(other.values())) if other else b""
    texts = [k for k in files if k.endswith(TEXT_EXT)]
    target = rng.random()
    if texts and target < 0.75:
        k = rng.choice(texts)
        files[k] = mutate(rng, files[k], other_b)
    else:
        i = rng.randrange(len(exs))
        exs[i] = mutate(rng, exs[i], other_b)
    ops = [("run", e) for e in exs[:3]]
    if rng.random() < 0.2:
        ops.append(("call", mutate(rng, b'{"method":"GET","path":"/api/orders?x=1","headers":{"a":"b"},"body":"","mediaType":"text/plain"}', other_b)))
    if rng.random() < 0.1:
        ops.append(("scaffold", mutate(rng, b'{"kind":"raml"}', other_b)))
    if rng.random() < 0.1:
        ops.append(("components", mutate(rng, b"db:select\nchoice\nhttp:request", other_b)))
    if rng.random() < 0.1:
        ops.append(("value", mutate(rng, b"run:0", other_b)))
    return files, ops


def run_one(bin_path, files, ops, timeout):
    d = tempfile.mkdtemp(prefix="mulay-fuzz-", dir=os.environ.get("FUZZ_TMP"))
    try:
        for k, v in files.items():
            p = os.path.join(d, "app", k)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(v)
        args = [bin_path, os.path.join(d, "app")]
        for i, (op, body) in enumerate(ops):
            p = os.path.join(d, "op%d" % i)
            open(p, "wb").write(body)
            args.append("%s:%s" % (op, p))
        env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=0:symbolize=1", MALLOC_ARENA_MAX="2")
        t0 = time.time()
        try:
            r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return "timeout", "TIMEOUT after %ss" % timeout, time.time() - t0
        err = r.stderr.decode("utf-8", "replace")
        if "AddressSanitizer" in err:
            m = re.search(r"ERROR: AddressSanitizer: (\S+).*?\n.*?#\d+ 0x[0-9a-f]+ in (\S+)", err, re.S)
            return "asan", (m.group(1) + " in " + m.group(2)) if m else "asan", time.time() - t0
        if r.returncode != 0:
            line = next((l for l in err.splitlines() if l.startswith("clay:") or "error" in l.lower()), err.strip()[:200])
            return "abort", re.sub(r"\d+", "N", line)[:200], time.time() - t0
        return "ok", "", time.time() - t0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def save(out, kind, sig, files, ops, detail):
    d = os.path.join(out, kind, re.sub(r"[^A-Za-z0-9_.-]+", "_", sig)[:80])
    if os.path.exists(d):
        return False
    for k, v in files.items():
        p = os.path.join(d, "app", k)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(v)
    for i, (op, body) in enumerate(ops):
        open(os.path.join(d, "op%d.%s" % (i, op)), "wb").write(body)
    open(os.path.join(d, "SIGNATURE"), "w").write(sig + "\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=2000)
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("-t", type=float, default=10.0)
    ap.add_argument("--seed", type=int, default=int(time.time()))
    ap.add_argument("--out", default=os.path.join(REPO, "target", "fuzz"))
    a = ap.parse_args()
    if a.j > 4:
        sys.exit("-j は 4 まで (このマシンは 4 コアまで)")
    bin_path = os.environ.get("FUZZ_BIN", os.path.join(REPO, "target", "fuzz-entry"))
    build(bin_path)
    ss = seeds()
    lock = threading.Lock()
    stats = {"ok": 0, "asan": 0, "abort": 0, "timeout": 0}
    found = []
    counter = [0]

    def worker(wid):
        rng = random.Random(a.seed * 31 + wid)
        while True:
            with lock:
                if counter[0] >= a.n:
                    return
                counter[0] += 1
            files, ops = case(rng, ss)
            kind, sig, dt = run_one(bin_path, files, ops, a.t)
            with lock:
                stats[kind] += 1
                if kind != "ok" and save(a.out, kind, sig, files, ops, ""):
                    found.append((kind, sig))
                    print("NEW %-7s %s" % (kind, sig), flush=True)

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(a.j)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    print("seed %d: %s, distinct findings %d (%s)" % (a.seed, stats, len(found), a.out))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
