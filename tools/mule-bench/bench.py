import json, os, signal, statistics, subprocess, sys, threading, time, urllib.request

CPUS = os.environ.get("BENCH_CPUS", "0-3")
CLIENT_CPU = os.environ.get("BENCH_CLIENT_CPU", "3")
CASES = ["copy", "csv2json", "json2xml", "xml2json", "json-filter", "json-agg"]


def rss_kb(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except OSError:
        return 0
    return 0


def get(port, path, timeout=900):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return r.status, r.read()


def one(pid, cg, port, path):
    os.sync()
    peak = [rss_kb(pid)]
    stop = threading.Event()

    def sample():
        while not stop.is_set():
            peak[0] = max(peak[0], rss_kb(pid))
            time.sleep(0.01)
    th = threading.Thread(target=sample); th.start()
    perf = subprocess.Popen(["perf", "stat", "-x", ",", "-a", "-C", CPUS, "-e", "cycles,instructions",
                             "--for-each-cgroup", cg], stderr=subprocess.PIPE, text=True)
    time.sleep(0.05)
    try:
        t0 = time.perf_counter()
        status, body = get(port, path)
        dt = time.perf_counter() - t0
    except Exception as e:
        status, body, dt = 0, repr(e).encode(), 0
    finally:
        perf.send_signal(signal.SIGINT)
        err = perf.communicate()[1]
        stop.set(); th.join()
    cnt = {}
    for line in err.splitlines():
        f = line.split(",")
        if len(f) > 2 and f[0].strip().isdigit():
            cnt[f[2]] = int(f[0])
    if status != 200 or body != b"ok":
        raise SystemExit(f"{path}: {status} {body[:300]!r}")
    return dt, cnt.get("cycles", 0), cnt.get("instructions", 0), peak[0]


def main():
    pid, cg, port, d, o, label = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
    warm, runs = int(os.environ.get("BENCH_WARM", "2")), int(os.environ.get("BENCH_RUNS", "3"))
    cases = sys.argv[7:] or CASES
    os.sched_setaffinity(0, {int(CLIENT_CPU)})
    idle = rss_kb(pid)
    res = {"label": label, "idle_rss_kb": idle, "cases": {}}
    for c in cases:
        q = f"/{c}?d={d}&o={o}" + ("&f=big.bin" if c == "copy" else "")
        for _ in range(warm):
            one(pid, cg, port, q)
        xs = [one(pid, cg, port, q) for _ in range(runs)]
        r = {"ms": statistics.median(x[0] for x in xs) * 1000,
             "cycles": statistics.median(x[1] for x in xs),
             "instructions": statistics.median(x[2] for x in xs),
             "peak_rss_kb": max(x[3] for x in xs)}
        res["cases"][c] = r
        print(f"{label:6} {c:12} {r['ms']:9.0f} ms  {r['cycles']/1e9:7.2f} Gcyc  {r['instructions']/1e9:7.2f} Ginsn  "
              f"peak RSS {r['peak_rss_kb']/1024:7.0f} MB", file=sys.stderr, flush=True)
    res["idle_after_kb"] = rss_kb(pid)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
