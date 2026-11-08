# 062 — DB の値と失敗は、JDBC ドライバが返す Java の型と例外の区別で持つ

状態: **採用** (2026-09-30、9e7932e。CBigInt・CLdt・CTime・CZoned は 2026-10-10、c989f6e)

## 決定
- ドライバ (db/sqlite、db/pg、db/oracle、db/mysql) は共通の `mulay.db.sql/Cell` で列の値を返す。腕は JDBC の
  `getObject` が返す Java の型に 1 対 1 で合わせる (CInt = Integer、CLong = Long、CDouble = Double、CFloat = Float、
  CDecimal = BigDecimal、CStr = String、CBytes = byte[]、CBool = Boolean、CDate = java.sql.Date、CTimestamp =
  java.sql.Timestamp、CBigInt = BigInteger、CLdt = LocalDateTime、CTime = java.sql.Time)。conn/db がこれを
  Java の class のメタデータ付きの DW の値にする。
- 数の綴りを持つ腕は文字列で持つ: CFloat は Java の `Float.toString` の綴り、CDecimal と CBigInt は 10 進の綴り。
- `CZoned` はパラメータだけに使う (DW の DateTime を ISO の綴りで)。時間帯の扱いはドライバが決め、決めていない
  ドライバは文字列として送る。
- `CDatum` はドライバ固有の Java オブジェクト (Oracle の oracle.sql.TIMESTAMP、ROWID など)。Mule はこれを bean
  `{length, [timeZone], null, stream, bytes}` にする。`CClob` は CLOB の中身で、Mule は class の無い String にする。
- 失敗は `sql/DbErr`: msg は JDBC の `SQLException#getMessage` と同じ文言 (Mule の error.description になる)、
  state は SQLState、exc はドライバが投げる SQLException の class (Mule のエラーの型を決める)。
- 結果は `Outcome` (rows、count は select なら -1、keys は生成されたキーの行)。ストアドプロシージャは
  `SpParam` (dir は IN / OUT / INOUT、type は JDBC の型の名前、"" なら指定なし) と `SpResult`。

## 理由
- 実 Mule の出力 (DW の値の class、エラーの型と description) は JDBC ドライバが返す Java の型と例外で決まる。
  ドライバの層で同じ区別を持てば、conn/db は DB の種類を知らずに Mule と同じ値とエラーを作れる。

## 場所
- `mulay.db.sql/Cell`、`mulay.db.sql/DbErr`、`mulay.db.sql/Outcome`、`mulay.db.sql/SpParam`、`mulay.db.sql/SpResult`
