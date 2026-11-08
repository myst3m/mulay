#!/usr/bin/env python3
# mulay だけの拡張 PKCE (mulay.salesforce.pkce=true) を実 org で手で確かめる。実 Mule は PKCE を送らないので
# シナリオ (scenario.scn) では比べられない。
#
#   mulay run test/fixtures/apps/salesforce-oauth mulay.salesforce.pkce=true &
#   python3 test/fixtures/apps/salesforce-oauth/pkce-check.py
#
# 認可は sf CLI の d30 のセッション (frontdoor.jsp) で通す (mule-oracle の sfauth と同じ)。トークンと認可コードは出さない。
import json, subprocess, urllib.request, urllib.parse, urllib.error, http.cookiejar, re
P = 18172
def get(path, method="GET"):
    req = urllib.request.Request(f"http://localhost:{P}{path}", method=method, data=b"" if method == "POST" else None, headers={"Content-Type": ""} if method == "POST" else {})
    try:
        r = urllib.request.urlopen(req, timeout=60); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
mask = lambda s: re.sub(r'(client_id|code_challenge|code)=[^&\s\']+', r'\1=***', re.sub(r'https://[^/\s]+/', 'https://***/', s))
print("GET /org (before):", *get("/org"))
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op0 = urllib.request.build_opener(NoRedir)
try:
    op0.open(f"http://localhost:{P}/authorize", timeout=30)
except urllib.error.HTTPError as e:
    loc = e.headers.get("Location", "")
    print("GET /authorize:", e.code, mask(loc))
d = json.loads(subprocess.run(["sf", "org", "display", "-o", "d30", "--json"], capture_output=True, text=True).stdout)["result"]
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(d["instanceUrl"] + "/secur/frontdoor.jsp?sid=" + urllib.parse.quote(d["accessToken"]), timeout=60).read()
url = f"http://localhost:{P}/authorize"
for hop in range(3):
    try:
        r = op.open(url, timeout=60); st, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        st, body = e.code, e.read().decode()
    m = re.search(r"window\.location\.replace\('(http://localhost:%d/[^']*)'\)" % P, body)
    if st != 200 or not m: break
    print("  (Salesforce の JS のリダイレクトでコールバックへ)")
    url = m.group(1)
print("authorize -> callback:", st, mask(body[:200]))
print("GET /org (after):", *get("/org"))
print("POST /unauthorize:", *get("/unauthorize", "POST"))
print("GET /org (after unauthorize):", *get("/org"))
