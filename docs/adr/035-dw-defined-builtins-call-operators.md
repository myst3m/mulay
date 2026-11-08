# 035 — DW で書かれた標準関数はネイティブで書き、定義と同じ順で同じ演算子を呼ぶ

状態: **採用** (2026-09-28 の記録。初期取り込みからこの形)

## 決定
- 実 DW で DW 自身により書かれた標準関数 (Core.dwl の flatMap・sum・maxBy・joinBy、Arrays.dwl、Objects.dwl、Strings.dwl の
  leftPad・substring、Tree.dwl、Values.dwl、Diff.dwl など) は、.dwl を解釈せずにネイティブで書く。ただし
  - その定義と同じ順で callback を呼び、
  - 定義が使う演算子 (`+`、`>`、`/` など) は dw::Core の組み込みを Env 経由で呼ぶ (`mulay.dw.lib.core_coll/op`)。
  失敗の文言は演算子の実装に従うので、実 DW と同じになる。
- DW の `if` で判定する条件 (Arrays / Objects の condition) は Boolean 以外を失敗にする (`if-bool`)。filter などの
  criteria は String の "true" / "false" を変換する (`to-bool`)。どちらを使うかは定義の書き方に合わせる。
- dw::util::Coercions の関数は `value as T {..}` の薄い包みなので、`mulay.dw.coerce/coerce` に委ねる (変換の意味を二重に持たない)。
- 組み込みの各実装は、引数の型がオーバーロードの型に合っていることを前提にしてよい (rt/invoke が照合済み)。
- 同じ名前の組み込みのオーバーロードは複数のファイルに分けてよい。engine が登録順にまとめるので、ファイルの中と
  ファイル間の登録の順がオーバーロードの順になる (core_dates の日時版は core の版の後ろ。core_text は String 版と
  Null 版だけを持ち、Array 版などは他のファイル)。

## 理由
- callback を呼ぶ順と、演算子の失敗の文言が実 DW と揃う。演算子を直接計算せず Env 経由で呼ぶので、型の組み合わせごとの
  失敗は演算子の実装 1 か所が決める。
- Coercions を coerce に委ねるので、書式・日時・単位・encoding の意味が `as` と常に一致する。

## 場所
- `mulay.dw.lib.core_coll/op`、`mulay.dw.lib.core_coll/call`、`mulay.dw.lib.core_coll/if-bool`、`mulay.dw.lib.core_coll/to-bool`
- `mulay.dw.lib.arrays/test1`、`mulay.dw.lib.coercions/as-with`
- 各 `mulay.dw.lib.*/builtins` (登録の順)

## 注意
- オーバーロードの登録の順を並べ替えない (実 DW の選択の順が変わる)。
