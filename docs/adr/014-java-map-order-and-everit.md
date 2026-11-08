# 014 — Java の Map の反復順と everit の違反の並びは、ハッシュと表の手順を写して再現する

状態: **採用** (2026-09-29、ca4fceb。キーの重複の除去を表で引くのは 2026-10-04、0058dfe)

## 決定

### `mulay.lib.jhash`

- Java の実装が Map に入れた値を外に出すときの並び (Mule のコネクタが返す Map、everit のプロパティの検証順) を、ハッシュと表の
  手順を写して再現する。
- java.util.HashMap (`hashmap-order`、`hashmap-order-with`): String#hashCode (UTF-16 の単位で計算した 32 ビットの値)。容量は 16
  (new HashMap<>(initial) なら initial 以上の 2 の冪) から始め、要素数が容量の 3/4 を超えるたびに倍にする (既定の負荷係数)。
  同じバケットの中は入れた順。重複した名前は最初の位置に 1 つだけ残す。
- バケットの木化 (1 バケットに 8 個以上、容量 64 以上) は扱わない。その場合は順が違いうる。
- Scala 2.12 の immutable.HashMap (`scala-map-order`): 4 件以下は Map1〜Map4 で足した順。5 件以上は HashTrieMap で、改良した
  ハッシュ (HashMap#improve) の下位 5 ビットずつで分けた順、同じハッシュは足した順。
- commons-collections4 の CaseInsensitiveMap (`commons-order`): 鍵は小文字にしたもの (同じ鍵は最初の位置)。ハッシュは JDK 1.4 の
  補助関数、反復は大きい桶から、桶の中は新しいものが先。倍にするときは古い桶を大きい方から順に新しい桶の先頭へ移す。

### `mulay.lib.jsonschema`

- JSON Schema (draft 4 と OpenAPI 3.0 の Schema Object) の検証。値もスキーマも `mulay.lib.yaml` の YVal。文言と並びは
  everit-json-schema (Mule の APIkit が使う) に合わせる。
- 並び: everit の検証順 (オブジェクトのプロパティは java.util.HashMap の反復順、配列は添字順) で違反を集め、入れ子の違反は
  「その階層の単独の違反が先、まとまった違反 (2 つ以上) は後」で平らにし (ValidationException#getAllMessages と同じ)、最後に
  全体を逆順にする (APIkit の出力と同じ)。
- format は date、date-time、time、email、uri、ipv4、ipv6、hostname だけ検査し、それ以外は検査しない。
- multipleOf で余りを求めると桁を展開しすぎる数 (1e999999999 と 0.01) は、計算せずに倍数でないとする (`number-fails`)。
- 重複を除いた名前 (`distinct-names`) は、見た名前を表で引く。

## 理由

- 実 Mule の出力の並びは Java の Map の実装で決まる。並びを合わせないと応答の JSON やエラーの並びが実 Mule と違う。
- キーの重複の除去はキーの数の 2 乗で、1MB のオブジェクトに 27〜110 秒かかった (APIkit の要求の検証で、攻撃者のキーの数の 2 乗の
  時間を使えた。0058dfe)。

## 場所

- `mulay.lib.jhash/string-hash`、`hashmap-order`、`hashmap-order-with`、`scala-map-order`、`improve`、`commons-order`、`commons-hash`、`rehash`
- `mulay.lib.jsonschema/validate`、`number-fails`、`distinct-names`、`format-fail`

## 関連
- ADR 037 (dw 側で同じ順序を再現する所)
