#!/usr/bin/env python3
"""Generate src/mulay/lib/unitab.clay (Unicode tables for mulay.lib.uni).

Sources
  - General category, full (special) case mappings, assigned code points:
    python3's `unicodedata` (its version is recorded in the output).
  - Simple case mappings (UnicodeData.txt fields 12-14), binary properties
    (PropList.txt / DerivedCoreProperties.txt), Scripts.txt, Blocks.txt,
    PropertyValueAliases.txt: the UCD files under /usr/share/unicode (Debian's
    unicode-data package). Their version can be newer than python's; every
    per-code-point property taken from them is restricted to the code points
    python's unicodedata reports as assigned, so the tables describe one
    repertoire.

Table encoding (all tables are Clay string literals, fixed-width records of
hex digits, sorted, searched by binary search in mulay.lib.uni; a string
literal costs nothing at start-up and a Clay vector literal of this size
crashes the compiler):
  GC        7 bytes : start(6) cat(1: "a"+id)           full coverage of 0..10FFFF
  *-RUNS    20 bytes: lo(6) hi(6) stride(1) sign(1) delta(6)
                      every cp in lo..hi stepping by stride maps to cp+delta
  TITLE     12 bytes: cp(6) title(6)   only where title != simple upper
  SPUP      25 bytes: cp(6) n(1) cp1(6) cp2(6) cp3(6)  full upper, n > 1
  sets      12 bytes: lo(6) hi(6)
  SCRIPT    8 bytes : start(6) id(2)            full coverage
  BLOCKS    12 bytes: lo(6) hi(6), names in BLOCK-NAMES ("|" separated)

Usage: python3 tools/gen-unicode.py > src/mulay/lib/unitab.clay
"""
import sys
import unicodedata as ud

UCD = "/usr/share/unicode/"
MAXCP = 0x10FFFF

GC_NAMES = ["Cn", "Lu", "Ll", "Lt", "Lm", "Lo", "Mn", "Mc", "Me", "Nd", "Nl",
            "No", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk",
            "So", "Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co"]


def h6(n):
    return "%06X" % n


def assigned(cp):
    return ud.category(chr(cp)) != "Cn"


def parse_ranges(fname, want):
    """{prop: set(cp)} for the props in `want` from a UCD ranges file."""
    out = {w: set() for w in want}
    with open(UCD + fname, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            rng, prop = [x.strip() for x in line.split(";")[:2]]
            if prop not in out:
                continue
            if ".." in rng:
                lo, hi = [int(x, 16) for x in rng.split("..")]
            else:
                lo = hi = int(rng, 16)
            for c in range(lo, hi + 1):
                if assigned(c):
                    out[prop].add(c)
    return out


def to_ranges(cps):
    cps = sorted(cps)
    out = []
    for c in cps:
        if out and out[-1][1] == c - 1:
            out[-1][1] = c
        else:
            out.append([c, c])
    return out


def emit_set(name, cps):
    rs = to_ranges(cps)
    s = "".join(h6(lo) + h6(hi) for lo, hi in rs)
    return "(def %s \"%s\")\n" % (name, s)


def simple_maps():
    up, lo, ti = {}, {}, {}
    with open(UCD + "UnicodeData.txt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split(";")
            c = int(p[0], 16)
            if not assigned(c):
                continue
            if p[12]:
                up[c] = int(p[12], 16)
            if p[13]:
                lo[c] = int(p[13], 16)
            if p[14]:
                ti[c] = int(p[14], 16)
    # python's repertoire wins where its full mapping is a single code point
    # (the UCD files may be a newer version that added case pairs).
    for c in range(MAXCP + 1):
        if not assigned(c):
            continue
        for m, f in ((up, str.upper), (lo, str.lower), (ti, str.title)):
            r = f(chr(c))
            if len(r) == 1:
                if ord(r) == c and m is not ti:
                    m.pop(c, None)
                else:
                    m[c] = ord(r)
    return up, lo, ti


def runs(mapping):
    """Group {cp: target} into (lo, hi, stride, delta) runs."""
    items = sorted((c, t - c) for c, t in mapping.items() if t != c)
    out = []
    for c, d in items:
        if out:
            lo, hi, st, dd = out[-1]
            if dd == d and ((st == 0 and c - hi in (1, 2)) or (st and c - hi == st)):
                out[-1] = [lo, c, c - hi if st == 0 else st, d]
                continue
        out.append([c, c, 0, d])
    res = []
    for lo, hi, st, d in out:
        res.append((lo, hi, st or 1, d))
    return res


def emit_runs(name, rs):
    s = ""
    for lo, hi, st, d in rs:
        s += h6(lo) + h6(hi) + str(st) + ("-" if d < 0 else "+") + h6(abs(d))
    return "(def %s \"%s\")\n" % (name, s)


def main():
    o = []
    o.append("(ns mulay.lib.unitab)\n\n")
    o.append('(def UNICODE-VERSION "%s")\n' % ud.unidata_version)
    o.append('(def GC-NAMES "%s")\n\n' % "".join(GC_NAMES))

    # --- general category, full coverage ---------------------------------
    recs = []
    prev = None
    for c in range(MAXCP + 1):
        g = ud.category(chr(c))
        if g != prev:
            recs.append(h6(c) + chr(ord("a") + GC_NAMES.index(g)))
            prev = g
    o.append("(def GC \"%s\")\n\n" % "".join(recs))

    # --- case mappings ----------------------------------------------------
    up, lo, ti = simple_maps()
    # consistency check against python's full mappings where they are 1:1
    bad = 0
    for c in range(MAXCP + 1):
        if not assigned(c):
            continue
        u = chr(c).upper()
        if len(u) == 1 and ord(u) != up.get(c, c):
            bad += 1
    if bad:
        print("warning: %d simple upper mappings disagree with python" % bad, file=sys.stderr)
    o.append(emit_runs("UPPER-RUNS", runs(up)))   # simple uppercase mapping (Character.toUpperCase)
    o.append(emit_runs("LOWER-RUNS", runs(lo)))   # simple lowercase mapping (Character.toLowerCase)
    tdiff = sorted((c, ti.get(c, up.get(c, c))) for c in set(ti) | set(up)
                   if ti.get(c, up.get(c, c)) != up.get(c, c))
    # simple titlecase where it differs from simple uppercase
    o.append("(def TITLE \"%s\")\n" % "".join(h6(c) + h6(t) for c, t in tdiff))
    sp = []
    for c in range(MAXCP + 1):
        if not assigned(c):
            continue
        u = chr(c).upper()
        if len(u) > 1:
            assert len(u) <= 3
            cps = [ord(x) for x in u] + [0] * (3 - len(u))
            sp.append(h6(c) + str(len(u)) + "".join(h6(x) for x in cps))
    # full uppercase mappings longer than one code point (SpecialCasing)
    o.append("(def SPUP \"%s\")\n\n" % "".join(sp))

    # --- binary properties ------------------------------------------------
    # Derived properties are rebuilt from python's categories plus the Other_*
    # contributory lists, so that they agree with the GC table.
    dcp = parse_ranges("DerivedCoreProperties.txt", ["Case_Ignorable"])
    pl = parse_ranges("PropList.txt", ["White_Space", "Ideographic", "Other_Alphabetic",
                                       "Other_Lowercase", "Other_Uppercase"])
    cats = {}
    for c in range(MAXCP + 1):
        cats.setdefault(ud.category(chr(c)), set()).add(c)
    dcp["Lowercase"] = cats["Ll"] | pl["Other_Lowercase"]
    dcp["Uppercase"] = cats["Lu"] | pl["Other_Uppercase"]
    dcp["Alphabetic"] = (cats["Lu"] | cats["Ll"] | cats["Lt"] | cats["Lm"] | cats["Lo"]
                         | cats["Nl"] | pl["Other_Alphabetic"])
    o.append(emit_set("ALPHABETIC", dcp["Alphabetic"]))           # Character.isAlphabetic
    o.append(emit_set("LOWERCASE", dcp["Lowercase"]))             # Character.isLowerCase
    o.append(emit_set("UPPERCASE", dcp["Uppercase"]))             # Character.isUpperCase
    o.append(emit_set("CASE-IGNORABLE", dcp["Case_Ignorable"]))   # final sigma
    o.append(emit_set("WHITE-SPACE", pl["White_Space"]))          # \p{IsWhite_Space}
    o.append(emit_set("IDEOGRAPHIC", pl["Ideographic"]))          # Character.isIdeographic
    o.append("\n")

    # --- scripts ----------------------------------------------------------
    names = [("Unknown", "Zzzz")]
    long2short = {}
    with open(UCD + "PropertyValueAliases.txt", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line.startswith("sc "):
                continue
            p = [x.strip() for x in line.split(";")]
            long2short[p[2]] = p[1]
    sc_of = {}
    with open(UCD + "Scripts.txt", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            rng, sc = [x.strip() for x in line.split(";")]
            if sc not in [n for n, _ in names]:
                names.append((sc, long2short.get(sc, sc)))
            idx = [n for n, _ in names].index(sc)
            if ".." in rng:
                a, b = [int(x, 16) for x in rng.split("..")]
            else:
                a = b = int(rng, 16)
            for c in range(a, b + 1):
                if assigned(c):
                    sc_of[c] = idx
    assert len(names) < 256
    recs = []
    prev = None
    for c in range(MAXCP + 1):
        s = sc_of.get(c, 0)
        if s != prev:
            recs.append(h6(c) + "%02X" % s)
            prev = s
    # SCRIPT-NAMES: script id i is the i-th "Long,Short" entry
    o.append("(def SCRIPT-NAMES \"%s\")\n" % "|".join("%s,%s" % (n, s) for n, s in names))
    o.append("(def SCRIPT \"%s\")\n\n" % "".join(recs))

    # --- blocks -----------------------------------------------------------
    blocks = []
    with open(UCD + "Blocks.txt", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            rng, name = [x.strip() for x in line.split(";")]
            a, b = [int(x, 16) for x in rng.split("..")]
            blocks.append((a, b, name))
    o.append("(def BLOCKS \"%s\")\n(def BLOCK-NAMES \"%s\")\n"
             % ("".join(h6(a) + h6(b) for a, b, _ in blocks),
                "|".join(n for _, _, n in blocks)))
    sys.stdout.write("".join(o))


if __name__ == "__main__":
    main()
