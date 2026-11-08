#!/usr/bin/env python3
"""DW のソースの並びを実 DW パーサと mulay のパーサの両方で読み、AST のダンプを比べる。

  compare.py CASES_FILE [--golden OUT]
CASES_FILE: "@@@@" だけの行で区切った DW ソースの並び (先頭行が "@@@@ m" ならモジュール)。
--golden OUT: 実 DW の結果から golden ファイルを書く (mulay の結果は使わない)。
  "@@@@ ok" <src> "@@@@ =" <期待するダンプ>  /  "@@@@ err" <src>  (実 DW が拒否するもの)
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle2dump as o2d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# mulay が意図して実 DW と違う結果を出す例 (golden に入れない)。ソースの一部 -> 理由
KNOWN_DIFF = {
    'h#"$(': 'ns#"$(..)" (名前空間付きで名前を補間する選択子) は未対応 (診断を出す)',
}
ROOT = os.path.dirname(os.path.dirname(HERE))


def read_cases(path):
    if os.path.isdir(path):
        fs = sorted(f for f in os.listdir(path) if f.endswith('.dwl'))
        return [('m' if f.endswith('.mod.dwl') else 'e', open(os.path.join(path, f), encoding='utf-8').read()) for f in fs]
    cases = []
    mode = 'e'
    cur = None
    for line in open(path, encoding='utf-8').read().split('\n'):
        if line.startswith('@@@@'):
            if cur is not None:
                cases.append((mode, '\n'.join(cur).strip('\n')))
            mode = 'm' if line.strip() == '@@@@ m' else 'e'
            cur = []
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        cases.append((mode, '\n'.join(cur).strip('\n')))
    return [c for c in cases if c[1].strip()]


def dwdump_bin():
    out = os.environ.get('DWDUMP') or os.path.join(tempfile.gettempdir(), 'mulay-dwdump')
    subprocess.run(['clay', 'build', os.path.join(HERE, 'dwdump.clay'), '-o', out], check=True,
                   cwd=ROOT, capture_output=True)
    return out


def run_mine(items):
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as f:
        f.write(''.join(f'{m}\n{src}\x01\n' for m, src in items))
        name = f.name
    try:
        out = subprocess.run([dwdump_bin(), '-b', name], capture_output=True, check=True).stdout.decode()
    finally:
        os.unlink(name)
    res = [None] * len(items)
    for line in out.split('\n'):
        if '\t' in line:
            i, r = line.split('\t', 1)
            res[int(i)] = r
    assert all(r is not None for r in res), 'dwdump -b lost records'
    return res


def main():
    path = sys.argv[1]
    golden = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--golden' else None
    cases = read_cases(path)
    ores = o2d.run_oracle(cases)
    expected = []
    for (m, src), r in zip(cases, ores):
        if 'err' in r:
            expected.append(('err', r['err']))
        else:
            try:
                expected.append(('ok', o2d.convert(src, r['ast'])))
            except o2d.Unsupported as e:
                expected.append(('unsupported', str(e)))
    if golden:
        with open(golden, 'w', encoding='utf-8') as f:
            f.write('# 生成: tools/dwparse/compare.py (実 DW 2.11.2 のパーサの結果)。手で編集しない。\n')
            for (m, src), (k, v) in zip(cases, expected):
                if any(key in src for key in KNOWN_DIFF):
                    continue
                if k == 'ok':
                    f.write(f'@@@@ ok{" m" if m == "m" else ""}\n{src}\n@@@@ =\n{v}\n')
                elif k == 'err':
                    f.write(f'@@@@ err{" m" if m == "m" else ""}\n{src}\n')
        print(f'wrote {golden}: {sum(1 for k, _ in expected if k == "ok")} ok, '
              f'{sum(1 for k, _ in expected if k == "err")} err, '
              f'{sum(1 for k, _ in expected if k == "unsupported")} unsupported')
        return
    mine = run_mine(cases)
    bad = 0
    for (m, src), (k, v), got in zip(cases, expected, mine):
        if k == 'ok':
            if got != 'OK ' + v:
                bad += 1
                print(f'--- MISMATCH\n{src}\n  dw:    {v}\n  mulay: {got}')
        elif k == 'err':
            if got.startswith('OK'):
                bad += 1
                print(f'--- ACCEPTED (DW rejects: {v})\n{src}\n  mulay: {got}')
        else:
            if not got.startswith('OK'):
                print(f'--- (unsupported by converter: {v}) mulay rejects\n{src}\n  mulay: {got}')
    print(f'{len(cases)} cases, {bad} differ')


if __name__ == '__main__':
    main()
