import fs from 'node:fs';
import path from 'node:path';
// usage: node run.mjs <mulay.wasm> <app dir> [<called app dir>]
// With a called app, a second instance loads it and every http:request of the first app reaches it through env.mulay_http.
const [wasmPath, dir, calleeDir] = process.argv.slice(2);
import { instantiate } from './host.mjs';
const enc = new TextEncoder(), dec = new TextDecoder();
const bytes = fs.readFileSync(wasmPath);

function walk(d, rel = '') { let r = []; for (const e of fs.readdirSync(path.join(d, rel), { withFileTypes: true })) { const p = rel ? rel + '/' + e.name : e.name; if (e.isDirectory()) r = r.concat(walk(d, p)); else r.push(p); } return r; }
function pack(d) {
  const files = walk(d).filter(f => !f.startsWith('target/'));
  const parts = [];
  for (const f of files) { const b = fs.readFileSync(path.join(d, f)); parts.push(enc.encode(f + '\n' + b.length + '\n')); parts.push(b); }
  const total = parts.reduce((a, b) => a + b.length, 0); const packed = new Uint8Array(total); let k = 0; for (const p of parts) { packed.set(p, k); k += p.length; }
  return dec.decode(packed);
}

let callee = null;
if (calleeDir) {
  callee = await instantiate(bytes);
  const cm = JSON.parse(callee.call('load', pack(calleeDir)));
  console.log('callee flows', cm.flows?.length, 'diags', JSON.stringify(cm.diagnostics));
}
const t0 = performance.now();
const app = await instantiate(bytes, { route: callee ? (req) => { console.log('  bridged', req.method, req.url); return callee; } : null });
const t1 = performance.now();
const t2 = performance.now();
const model = app.call('load', pack(dir));
const t3 = performance.now();
const m = JSON.parse(model);
console.log('instantiate ms', (t1 - t0).toFixed(1), 'load ms', (t3 - t2).toFixed(1), 'flows', m.flows?.length, 'diags', JSON.stringify(m.diagnostics));
const exs = JSON.parse(fs.readFileSync(path.join(dir, 'livenote/examples.json'), 'utf8'));
for (let round = 0; round < (callee ? 1 : 3); round++) {
  for (const e of exs) {
    const a = performance.now(); const tr = JSON.parse(await app.run('run', JSON.stringify(e))); const b = performance.now();
    if (round === (callee ? 0 : 2)) console.log(e.id, 'total ms', (b - a).toFixed(2), 'flow ms', tr.ms, 'status', tr.response?.status, tr.response?.body?.preview ?? ('stopped ' + tr.stoppedAt), tr.steps.map(s => s.status[0]).join(''));
  }
}
const tr = JSON.parse(await app.run('run', JSON.stringify(exs[0])));
if (tr.response) console.log('getValue', app.call('get_value', tr.response.body.id).slice(0, 120));
console.log('components', app.call('components', 'db:select\nchoice\nfoo:bar\nvalidation:is-not-null\nhttp:request'));
if (app.out) console.log('stdout:', app.out.slice(0, 300)); if (app.err) console.log('stderr:', app.err.slice(0, 300));
