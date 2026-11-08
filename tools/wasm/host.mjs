// Default host for mulay.wasm (ADR 098): the env imports and the Str calling convention.
// With JSPI (Chrome), mulay_http suspends the wasm while JS awaits fetch, so run and call return Promises (st.run).
// Without JSPI (Node 22), mulay_http can only answer synchronously: a route to another instance, a sync opts.http, or "" (held).
const enc = new TextEncoder(), dec = new TextDecoder();
const SAFE = new Set(['GET', 'HEAD', 'OPTIONS']);
const ASYNC_EXPORTS = new Set(['run', 'call']);

export const hasJSPI = typeof WebAssembly.Suspending === 'function' && typeof WebAssembly.promising === 'function';

const b64 = (u8) => { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode(...u8.subarray(i, i + 0x8000)); return btoa(s); };
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
const connectivity = (req, why) => ({ error: { type: 'HTTP:CONNECTIVITY', description: `HTTP ${req.method} on resource '${req.url}' failed: ${why}.` } });

// An application may come from someone else, so fetchHttp sends nothing unless opts.allow(url) says yes, and never sends cookies.
// allowedUrl is a ready-made rule for opts.allow: public http(s) names and addresses only, not localhost, private or link-local
// networks (the cloud metadata address too), *.local or *.internal. Combine it with a list of allowed origins.
const v4private = (a) => a[0] === 0 || a[0] === 10 || a[0] === 127 || (a[0] === 169 && a[1] === 254) || (a[0] === 172 && a[1] >= 16 && a[1] <= 31)
  || (a[0] === 192 && a[1] === 168) || (a[0] === 100 && a[1] >= 64 && a[1] <= 127) || a[0] >= 224;
const v4 = (h) => { const m = /^(\d+)\.(\d+)\.(\d+)\.(\d+)$/.exec(h); return m ? m.slice(1).map(Number) : null; };
function privateHost(host) {
  const h = host.toLowerCase().replace(/^\[|\]$/g, '');
  if (h === 'localhost' || /\.(localhost|local|internal)\.?$/.test(h)) return true;
  const a = v4(h);
  if (a) return v4private(a);
  if (!h.includes(':')) return false;
  if (h === '::' || h === '::1' || /^f[cd]/.test(h) || /^fe[89ab]/.test(h)) return true;
  const m = /^::ffff:([0-9a-f]{1,4}):([0-9a-f]{1,4})$/.exec(h);
  if (m) { const x = parseInt(m[1], 16), y = parseInt(m[2], 16); return v4private([x >> 8, x & 255, y >> 8, y & 255]); }
  const d = /^::ffff:(\d+\.\d+\.\d+\.\d+)$/.exec(h);
  return d ? v4private(v4(d[1])) : false;
}
export function allowedUrl(url) {
  let u;
  try { u = new URL(url); } catch (e) { return false; }
  return (u.protocol === 'http:' || u.protocol === 'https:') && !privateHost(u.hostname);
}

async function readCapped(r, max) {
  if (!r.body) return new Uint8Array(await r.arrayBuffer());
  const reader = r.body.getReader(), parts = [];
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    n += value.length;
    if (n > max) { reader.cancel(); return null; }
    parts.push(value);
  }
  const out = new Uint8Array(n); let k = 0; for (const p of parts) { out.set(p, k); k += p.length; }
  return out;
}

// The network part: sends safe methods only unless allowWrites, only to URLs opts.allow(url) accepts (none without it),
// never with cookies, and reads at most opts.maxBytes (16 MiB). Returns the response object, or null when it does not send.
export async function fetchHttp(req, { allowWrites = false, allow = null, maxBytes = 16 * 1024 * 1024 } = {}) {
  if (typeof fetch !== 'function') return null;
  if (!allowWrites && !SAFE.has(req.method)) return null;
  if (!(allow && allow(req.url))) return connectivity(req, `${req.url} is not allowed from the browser (the host did not allow it; pass opts.allow to permit it)`);
  let r;
  try {
    const body = SAFE.has(req.method) ? undefined : (req.bodyBase64 ? unb64(req.bodyBase64) : req.body);
    r = await fetch(req.url, { method: req.method, headers: req.headers || {}, body, credentials: 'omit' });
  } catch (e) {
    return connectivity(req, (e && e.message) || 'network error (CORS or connection refused)');
  }
  const bytes = await readCapped(r, maxBytes);
  if (bytes === null) return connectivity(req, `the response is larger than ${maxBytes} bytes`);
  const headers = {};
  r.headers.forEach((v, k) => { headers[k.toLowerCase()] = v; });
  const res = { status: r.status, reason: r.statusText, headers, mediaType: headers['content-type'] || '' };
  try { res.body = new TextDecoder('utf-8', { fatal: true }).decode(bytes); } catch (e) { res.body = ''; res.bodyBase64 = b64(bytes); }
  return res;
}

const text = (x) => (x == null || x === '') ? '' : (typeof x === 'string' ? x : JSON.stringify(x));

// opts.route(req) may return another instance (from instantiate) to call instead of the network.
// opts.http(req) replaces the network part (it may be async with JSPI); opts.allowWrites lets fetchHttp send POST, PUT and so on;
// opts.allow(url) and opts.maxBytes are passed to fetchHttp.
export async function instantiate(bytes, opts = {}) {
  const st = { ex: null, out: '', err: '', jspi: hasJSPI };
  const put = (b) => { const p = st.ex.clay_alloc(b.length); new Uint8Array(st.ex.memory.buffer, p, b.length).set(b); return [p, b.length]; };
  const answer = (o, s) => { const res = enc.encode(s); const [q] = put(res); new DataView(st.ex.memory.buffer).setUint32(o, q, true); return res.length; };
  const request = (p, n) => JSON.parse(dec.decode(new Uint8Array(st.ex.memory.buffer, p, n).slice()));
  const callee = (req) => {
    const q = req.url.indexOf('?');
    return JSON.stringify({ method: req.method, path: req.path + (q < 0 ? '' : req.url.slice(q)), headers: req.headers, body: req.body, bodyBase64: req.bodyBase64, mediaType: req.mediaType });
  };
  const self = (req) => JSON.stringify(connectivity(req, 'an application cannot call itself here'));
  const asyncHttp = async (p, n, o) => {
    const req = request(p, n);
    const target = opts.route ? opts.route(req) : null;
    if (target === st) return answer(o, self(req));
    if (target) return answer(o, await target.run('call', callee(req)));
    return answer(o, text(await (opts.http ? opts.http(req) : fetchHttp(req, opts))));
  };
  const syncHttp = (p, n, o) => {
    const req = request(p, n);
    const target = opts.route ? opts.route(req) : null;
    if (target === st) return answer(o, self(req));
    if (target) return answer(o, target.call('call', callee(req)));
    const r = opts.http ? opts.http(req) : '';
    return answer(o, (r && typeof r.then === 'function') ? '' : text(r));
  };
  const env = {
    clay_wasm_write(fd, p, n) { const s = dec.decode(new Uint8Array(st.ex.memory.buffer, p, n)); if (fd === 1) st.out += s; else st.err += s; },
    clay_wasm_trap(code) { throw new Error('clay trap ' + code + ' ' + st.err); },
    clay_wasm_epoch_ms() { return Date.now(); },
    clay_wasm_mono_ms() { return performance.now(); },
    clay_wasm_sleep_ms(ms) { },
    clay_wasm_random(p, n) {
      try {
        const u = new Uint8Array(st.ex.memory.buffer, p, n);
        for (let i = 0; i < n; i += 65536) crypto.getRandomValues(u.subarray(i, Math.min(n, i + 65536)));
        return 0;
      } catch { return 1; }
    },
    mulay_http: hasJSPI ? new WebAssembly.Suspending(asyncHttp) : syncHttp,
  };
  const { instance } = await WebAssembly.instantiate(bytes, { env });
  st.ex = instance.exports;
  const finish = (o, len) => {
    const q = new DataView(st.ex.memory.buffer).getUint32(o, true);
    const r = dec.decode(new Uint8Array(st.ex.memory.buffer, q, len)); st.ex.clay_free(q); st.ex.clay_free(o); return r;
  };
  // load, get_value, components, scaffold: these never reach mulay_http.
  st.call = (name, s) => {
    const [p, n] = put(enc.encode(s)); const o = st.ex.clay_alloc(4);
    return finish(o, st.ex[name](p, n, o));
  };
  const promising = {};
  // run and call: they may reach mulay_http, so with JSPI they must go through WebAssembly.promising.
  st.run = async (name, s) => {
    if (!hasJSPI || !ASYNC_EXPORTS.has(name)) return st.call(name, s);
    const f = promising[name] || (promising[name] = WebAssembly.promising(st.ex[name]));
    const [p, n] = put(enc.encode(s)); const o = st.ex.clay_alloc(4);
    return finish(o, await f(p, n, o));
  };
  return st;
}
