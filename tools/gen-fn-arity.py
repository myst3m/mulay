#!/usr/bin/env python3
"""組み込み関数の引数のうち関数型のものの引数の数を、docs/dw-stdlib-catalog.md のシグネチャから作る。

  python3 tools/gen-fn-arity.py [mulay のルート]

出力: src/mulay/dw/fnarity.clay
  FN-ARITY  Map: "モジュール 名前" -> オーバーロードごとの [a0 a1 ..] (引数の位置ごとに、関数型ならその引数の数、
            そうでなければ -1)
  FN-TYPE   Map: "モジュール 名前 位置" -> その位置の関数型の綴り (最初のオーバーロードのもの。エラーの文言に使う)
  FN-SIG    Map: "モジュール 名前" -> オーバーロードごと (宣言の順) の "<最少> <最多> <既定値> (<型>, ..)"。最少は既定値の無い
            引数の数、既定値は引数ごとに既定値があれば 1 の列 (引数が無ければ "-")。
            どのオーバーロードの数にも合わない呼び出しの文言 (実 DW: "Expects `n` argument but got `m`. Expecting: (..)")
            に使う。型の綴りは実 DW の表示に寄せる ("{| a: T |}" → "{|a: T|}")
  FN-RET    Map: "モジュール 名前" -> 引数の型が分からないときの戻り値の型 (Number / String / Boolean / Array / Object。
            Null だけを受けるオーバーロードを除いた戻り値がすべて同じ単純な型のときだけ。静的な型の検査に使う)
カタログのシグネチャは DataWeave 2.11.2 の .dwl ソースの fun 宣言を写したもの。
"""
import os
import re
import sys


def split_top(s, sep=","):
    """括弧・山括弧・波括弧の外にある sep で分ける"""
    out, depth, cur = [], 0, ""
    i = 0
    while i < len(s):
        c = s[i]
        if c in "([{<" and not (c == "<" and s[i + 1:i + 2] == ":"):   # "<:" は括弧ではない
            depth += 1
        elif c in ")]}>":
            # "->" の > は括弧ではない
            if not (c == ">" and i > 0 and s[i - 1] == "-"):
                depth -= 1
        if c == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    out.append(cur)
    return out


def match_paren(s, i):
    """s[i] == '(' に対応する ')' の位置"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return -1


def fn_arity(ty):
    """型が関数型 (a, b) -> R ならその引数の数、そうでなければ -1"""
    t = ty.strip()
    if not t.startswith("("):
        return -1
    j = match_paren(t, 0)
    if j < 0 or not t[j + 1:].strip().startswith("->"):
        return -1
    inner = t[1:j].strip()
    if inner == "":
        return 0
    return len(split_top(inner))


def params_of(sig):
    """fun の宣言の引数の型の列"""
    # 名前の後の総称 <..> を飛ばして、引数の ( を探す
    i, depth = 0, 0
    while i < len(sig):
        c = sig[i]
        if c == "<" and sig[i + 1:i + 2] != ":":
            depth += 1
        elif c == ">" and sig[i - 1] != "-":
            depth -= 1
        elif c == "(" and depth == 0:
            break
        i += 1
    j = match_paren(sig, i)
    inner = sig[i + 1:j].strip()
    if inner == "":
        return []
    tys = []
    for p in split_top(inner):
        p = re.sub(r"@\w+(\([^)]*\))?\s*", "", p).strip()
        k = p.find(":")
        ty = p[k + 1:] if k >= 0 else "Any"
        # 既定値 (= ..) は落とす
        ty = split_top(ty, "=")[0]
        tys.append(ty.strip())
    return tys


def bounds_of(sig):
    """総称の宣言 <T <: Object, U> の上限 (型変数 -> 上限)"""
    m = re.match(r"^\s*[^\s(<]+\s*<(.*?)>\s*\(", sig)
    out = {}
    if not m:
        return out
    for g in split_top(m.group(1)):
        k = g.find("<:")
        if k >= 0:
            out[g[:k].strip()] = g[k + 2:].strip()
    return out


def params_full(sig):
    """(既定値の無い引数の数, 引数の型の列 (表示用), 既定値の有無の列 "01..")"""
    bounds = bounds_of(sig)
    i, depth = 0, 0
    while i < len(sig):
        c = sig[i]
        if c == "<" and sig[i + 1:i + 2] != ":":
            depth += 1
        elif c == ">" and sig[i - 1] != "-":
            depth -= 1
        elif c == "(" and depth == 0:
            break
        i += 1
    j = match_paren(sig, i)
    inner = sig[i + 1:j].strip()
    if inner == "":
        return 0, [], ""
    req, tys, mask = 0, [], ""
    for p in split_top(inner):
        p = re.sub(r"@\w+(\([^)]*\))?\s*", "", p).strip()
        k = p.find(":")
        ty = p[k + 1:] if k >= 0 else "Any"
        parts = split_top(ty, "=")
        if len(parts) == 1:
            req += 1
            mask += "0"
        else:
            mask += "1"
        t = re.sub(r"\s+", " ", parts[0].strip()).replace("{| ", "{|").replace(" |}", "|}")
        # 開いたオブジェクトの型は実 DW の表示 "{ K?: V }" (キーの括弧を外し、内側に空白)
        t = re.sub(r"\{\((\w+)\)(\??): ([^{}]*)\}", r"{ \1\2: \3 }", t)
        # 上限のある型変数そのものは上限で出す (entrySet<T <: Object>(obj: T) → Object)
        if t in bounds:
            t = bounds[t]
        tys.append(t)
    return req, tys, mask


SIMPLE = {"Number", "String", "Boolean", "Object"}


def ret_of(sig):
    """戻り値の型の単純な名前 (Array<..> は Array)。単純でなければ """""
    d, i = 0, 0
    close = -1
    while i < len(sig):
        c = sig[i]
        if c == "(" and d == 0 and close < 0:
            j = match_paren(sig, i)
            close = j
            break
        if c == "<" and sig[i + 1:i + 2] != ":":
            d += 1
        elif c == ">" and sig[i - 1] != "-":
            d -= 1
        i += 1
    rest = sig[close + 1:].strip()
    if not rest.startswith(":"):
        return ""
    r = rest[1:].strip()
    if r in SIMPLE:
        return r
    if r.startswith("Array<") and r.endswith(">") and "|" not in r:
        return "Array"
    return ""


def null_only(sig):
    tys = params_of(sig)
    return len(tys) > 0 and all(t.strip() in ("Null", "Nothing") for t in tys[:1])


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    lines = open(os.path.join(root, "docs/dw-stdlib-catalog.md"), encoding="utf-8").read().splitlines()
    module, name = None, None
    arity, ftype, rets, sigs = {}, {}, {}, {}
    for ln in lines:
        m = re.match(r"^## (dw::\S+)$", ln)
        if m:
            module = m.group(1)
            continue
        if module is None or not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.replace("\\|", "\x00").split("|")]
        if len(cells) < 3 or not cells[2].startswith("`"):
            continue
        if cells[1].startswith("`"):
            name = cells[1].strip("`")
        sig = cells[2].strip("`").replace("\x00", "|")
        tys = params_of(sig)
        key = module + " " + name
        arity.setdefault(key, []).append([fn_arity(t) for t in tys])
        req, full, mask = params_full(sig)
        sigs.setdefault(key, []).append(str(req) + " " + str(len(full)) + " " + (mask or "-") + " (" + ", ".join(full) + ")")
        if not null_only(sig):
            rets.setdefault(key, []).append(ret_of(sig))
        for i, t in enumerate(tys):
            if fn_arity(t) >= 0:
                ftype.setdefault(key + " " + str(i), t)
    out = []
    out.append("(ns mulay.dw.fnarity)\n")
    def lit(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    out.append("(def FN-ARITY: Map(Str Vec(Vec(Int)))\n  {" + "\n   ".join(
        lit(k) + " [" + " ".join("[" + " ".join(str(a) for a in x) + "]" for x in v) + "]" for k, v in sorted(arity.items())) + "})\n")
    out.append("(def FN-TYPE: Map(Str Str)\n  {" + "\n   ".join(
        lit(k) + " " + lit(v) for k, v in sorted(ftype.items())) + "})")
    out.append("\n(def FN-SIG: Map(Str Vec(Str))\n  {" + "\n   ".join(
        lit(k) + " [" + " ".join(lit(x) for x in v) + "]" for k, v in sorted(sigs.items())) + "})")
    ret1 = {k: v[0] for k, v in rets.items() if v and v[0] != "" and all(x == v[0] for x in v)}
    out.append("\n(def FN-RET: Map(Str Str)\n  {" + "\n   ".join(lit(k) + " " + lit(v) for k, v in sorted(ret1.items())) + "})")
    open(os.path.join(root, "src/mulay/dw/fnarity.clay"), "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
