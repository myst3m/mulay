// node tools/wasm/host_test.mjs <mulay.wasm>: host.mjs without JSPI (Node 22) and fetchHttp with a fake fetch.
// The JSPI path runs in Chrome: tools/wasm/chrome_test.sh <mulay.wasm>.
import fs from 'node:fs';
import { instantiate, fetchHttp as fetchRaw, allowedUrl, hasJSPI } from './host.mjs';
const fetchHttp = (req, o = {}) => fetchRaw(req, { allow: allowedUrl, ...o });
let bad = 0;
const check = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const seen = [];
globalThis.fetch = async (url, init) => {
  seen.push({ url, init });
  if (url.includes('down')) throw new TypeError('Failed to fetch');
  const bin = url.includes('bin');
  const body = bin ? new Uint8Array([0, 255, 67]) : new TextEncoder().encode(url.includes('missing') ? '' : '{"name":"A"}');
  return new Response(body, { status: url.includes('missing') ? 404 : 200, headers: { 'Content-Type': bin ? 'application/octet-stream' : 'application/json', 'X-From': 'real' } });
};
const g = await fetchHttp({ method: 'GET', url: 'http://x/a', headers: { 'X-A': '1' } });
check('GET goes out', g.status === 200 && g.body === '{"name":"A"}' && g.headers['x-from'] === 'real' && seen[0].init.headers['X-A'] === '1');
check('POST is not sent by default', (await fetchHttp({ method: 'POST', url: 'http://x/a', headers: {} })) === null && seen.length === 1);
const p = await fetchHttp({ method: 'POST', url: 'http://x/a', headers: {}, body: '', bodyBase64: '/wBB' }, { allowWrites: true });
check('POST with allowWrites sends base64 bodies as bytes', p.status === 200 && seen[1].init.body instanceof Uint8Array && seen[1].init.body[0] === 255);
check('binary responses come back as base64', (await fetchHttp({ method: 'GET', url: 'http://x/bin', headers: {} })).bodyBase64 === 'AP9D');
check('network error is HTTP:CONNECTIVITY', (await fetchHttp({ method: 'GET', url: 'http://down/a', headers: {} })).error.type === 'HTTP:CONNECTIVITY');
check('no cookies or credentials are sent', seen[0].init.credentials === 'omit');
const n0 = seen.length;
for (const u of ['http://localhost:8080/x', 'http://LOCALHOST/x', 'http://127.0.0.1/x', 'http://127.9.9.9/x', 'http://10.1.2.3/x', 'http://172.16.0.1/x',
                 'http://172.31.255.255/x', 'http://192.168.1.1/x', 'http://169.254.169.254/latest', 'http://0.0.0.0/x', 'http://[::1]/x',
                 'http://[fd00::1]/x', 'http://[fe80::1]/x', 'http://[::ffff:127.0.0.1]/x', 'http://2130706433/x', 'http://0x7f.1/x',
                 'http://printer.local/x', 'http://db.internal/x', 'http://a.localhost/x', 'file:///etc/passwd', 'data:text/plain,a', 'blob:http://x/1', 'ftp://x/a']) {
  const r = await fetchHttp({ method: 'GET', url: u, headers: {} });
  check('refused by allowedUrl: ' + u, r && r.error && r.error.type === 'HTTP:CONNECTIVITY' && /not allowed/.test(r.error.description));
}
check('refused URLs never reach fetch', seen.length === n0);
check('public names still go out', (await fetchHttp({ method: 'GET', url: 'https://api.example.com/a', headers: {} })).status === 200);
check('172.32.0.1 is public', (await fetchHttp({ method: 'GET', url: 'http://172.32.0.1/a', headers: {} })).status === 200);
const al = await fetchHttp({ method: 'GET', url: 'http://localhost:8081/a', headers: {} }, { allow: (u) => u.startsWith('http://localhost:8081/') });
check('opts.allow lets a chosen URL through', al.status === 200);
const n1 = seen.length;
const dflt = await fetchRaw({ method: 'GET', url: 'https://api.example.com/a?k=secret', headers: {} });
check('without opts.allow nothing is sent, public names included', dflt && dflt.error && dflt.error.type === 'HTTP:CONNECTIVITY' && /not allowed/.test(dflt.error.description) && seen.length === n1);
const big = await fetchHttp({ method: 'GET', url: 'http://x/a', headers: {} }, { maxBytes: 4 });
check('responses over maxBytes are refused', big.error && /larger than 4 bytes/.test(big.error.description));
check('no JSPI in this Node', hasJSPI === false);
const bytes = fs.readFileSync(process.argv[2]);
const callee = await instantiate(bytes);
callee.call('load', pack('test/fixtures/livenote/customer-sys'));
const app = await instantiate(bytes, { route: (req) => req.url.includes('customer-sys') ? callee : null });
app.call('load', pack('test/fixtures/livenote/linked'));
const t = JSON.parse(await app.run('run', JSON.stringify({ id: 'ok', flow: 'orders', request: { method: 'GET', path: '/orders/7' } })));
check('route to another instance without JSPI', t.response.status === 200 && JSON.parse(app.call('get_value', t.response.body.id)).text.includes('"tenant": "acme"'));
const lone = await instantiate(bytes);
lone.call('load', pack('test/fixtures/livenote/linked'));
const h = JSON.parse(await lone.run('run', JSON.stringify({ id: 'ok', flow: 'orders', request: { method: 'GET', path: '/orders/7' } })));
check('no route and no JSPI: held', h.stoppedAt === 'orders/processors/0');
const deep = await instantiate(bytes);
deep.call('load', pack('test/fixtures/livenote/deep-recursion'));
const rec = async (n) => { try { return JSON.parse(await deep.run('run', JSON.stringify({ id: 'r', flow: 'rec', request: { method: 'POST', path: '/rec', mediaType: 'application/json', body: JSON.stringify({ n }) } }))); } catch (e) { return { thrown: String(e.message) }; } };
const d1 = await rec(600);
check('deep recursion fails with Stack Overflow instead of exhausting the wasm stack', d1.response && d1.response.status === 500 && /Max stack is 1000/.test(d1.response.body.preview));
const d2 = await rec(100);
check('the instance still runs after a Stack Overflow', d2.response && d2.response.status === 200 && d2.response.body.preview.trim() === '5050');
const realFill = crypto.getRandomValues.bind(crypto);
let filled = 0;
crypto.getRandomValues = (a) => { filled += a.length; return realFill(a); };
const sc = await instantiate(bytes);
sc.call('load', pack('test/fixtures/livenote/scaffold-ids'));
const ids = sc.call('scaffold', JSON.stringify({ config: 'orders-config' })).match(/doc:id=\\"[0-9a-f-]{36}/g) || [];
check('scaffold doc:ids come from the host random (crypto.getRandomValues)', ids.length >= 2 && new Set(ids).size === ids.length && filled >= 16 * ids.length);
crypto.getRandomValues = realFill;
crypto.getRandomValues = () => { throw new Error('no entropy'); };
const nr = await instantiate(bytes);
nr.call('load', pack('test/fixtures/livenote/scaffold-ids'));
let nrOut;
try { nrOut = nr.call('scaffold', JSON.stringify({ config: 'orders-config' })); } catch (e) { nrOut = { thrown: String(e.message) }; }
check('without host random, scaffold stops instead of making ids from a weak fallback', nrOut && nrOut.thrown && /random/.test(nrOut.thrown));
crypto.getRandomValues = realFill;
process.exit(bad ? 1 : 0);

function walk(d, rel = '') { let r = []; for (const e of fs.readdirSync(d + '/' + rel, { withFileTypes: true })) { const q = rel ? rel + '/' + e.name : e.name; if (e.isDirectory()) r = r.concat(walk(d, q)); else r.push(q); } return r; }
function pack(d) { return walk(d).map((f) => { const b = fs.readFileSync(d + '/' + f, 'utf8'); return f + '\n' + Buffer.byteLength(b) + '\n' + b; }).join(''); }
