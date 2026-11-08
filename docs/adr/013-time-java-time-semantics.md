# 013 — 日時は java.time と同じ意味で自作し、タイムゾーンの規則は OS の zoneinfo から読む

状態: **採用** (2026-09-28)

## 決定

### 型と計算

- `mulay.lib.time.types` の型は DataWeave の日時型と 1 対 1 に対応し、java.time の同名クラスと同じ意味を持つ (Date = LocalDate、
  Time = OffsetTime、DateTime = ZonedDateTime (zone が TzOffset なら OffsetDateTime)、TimeZone = ZoneOffset / ZoneRegion、
  Period = DwPeriod (Period か Duration))。
- 値はすべて正規化済みで作る (ns は 0..999999999、offset は -64800..64800 秒)。types の `->X` は検査しない。検査付きの構築は
  `mulay.lib.time.local`・`amount`・`zoned` に置き、err の文言は java.time の例外メッセージに合わせる。
- 暦は先発グレゴリオ暦 (IsoChronology と同じ規則)。年は Java と同じく -999999999 .. 999999999。通日は Hinnant の days_from_civil。
  週の計算は WeekFields.ComputedDayOfField と同じ。
- ゾーン付きの加算は ZonedDateTime と同じ: 日付系 (Period) はローカル日時で足して ofLocal で解決する (ギャップは遷移の長さだけ
  後ろへずらし、オーバーラップは元のオフセットが有効ならそれを、でなければ早い方を使う)。時間系 (Duration) は瞬間で足す。
  `zdt-until` は b を a のゾーンへ移してから、日付系はローカル日時、時間系は瞬間で数える。

### 書式 (`mulay.lib.time.fmt`)

- DateTimeFormatter.ofPattern(p, Locale.US) のパターン言語。解析の既定は SMART resolver (`with-resolver` で LENIENT / STRICT)。
  週の定義は既定で Locale.US (日曜始まり、最初の週の最小日数 1)。エラーの文言は Java の例外メッセージと同じ
  (ただし "Unable to obtain .. from TemporalAccessor: .." の TemporalAccessor の部分は完全には一致しない)。
- Java 17 と意図して同じにしている癖: 'F' は ALIGNED_DAY_OF_WEEK_IN_MONTH。NARROW の月名・曜日名の逆引きは後勝ち ("J" は 7 月)。
  z の解析で "UTC" の後に +/- 以外が続くと名前の表から Etc/UTC になる。'a' や 'B' だけで時が無いときはその区間の中点の時刻
  (AM → 06:00。JDK 16 以降)。数の解析で 19 桁を超えて溢れたら 1 桁減らす (Java の BigInteger の扱い)。
- 地域の名前と週の定義 (`mulay.lib.time.locales`) と時間帯の名前 (`mulay.lib.time.names`) は生成物 (手で編集しない)。locales は
  tools/gen-locale-data.java (JDK 17.0.21-ea、CLDR)、names は tools/gen-time-golden.java (JDK の tzdb 2026b、Locale.US)。
  表に無い地域は言語で、それも無ければ en-US で引く (違いは docs/compat/deviations.md のロケールの行)。

### タイムゾーン (`mulay.lib.time.tz`)

- システムのタイムゾーン (`now()`、ファイルの時刻など) は、環境変数 TZ、無ければ /etc/timezone、無ければ /etc/localtime の
  リンク先から決め、TZ の値ごとに覚えて読み直さない (`mulay.lib.time.tz/system-zone`)。JVM も既定のタイムゾーンを起動時に決めて
  変えない。以前は `now()` のたびに /etc/timezone を開き /etc/localtime を readlink していた (要求 1 件で 2 回のシステムコール)。
  TZ の値が変われば求め直すので、fixture ごとに TZ を変える dwt はそのまま動く。
- 規則は $TZDIR (未設定なら /usr/share/zoneinfo) の TZif (v1/v2/v3) と、その footer の POSIX TZ 文字列 (将来の規則) から読む。
  ゾーン ID の別名 (US/Eastern など) はファイルシステムにあるものをそのまま使う。別名のファイルが無い (Debian で tzdata-legacy が
  入っていないなど) ときは $TZDIR/tzdata.zi の "L 実体 別名" の行で実体を引く。
- ファイルが無くても UTC・GMT・UT と固定オフセット (+09:00、GMT+9 など) は常に使える。読んだ規則はキャッシュする (ADR 001)。
- POSIX TZ 文字列に規則が無ければ米国の既定 (M3.2.0,M11.1.0)。
- 負の夏時間の時代 (Europe/Dublin): Java (rearguard) と同じく footer の dst 側を標準とみなす (`parse-tzif`、`dst-at?`、`std-offset-at`)。
- 標準オフセット (ZoneRules.getStandardOffset): TZif に標準オフセットそのものは無いので、夏時間中は前後の標準時の型のうちオフセットが
  近い方を使う。日付変更線を越えた Pacific/Apia のように標準も変わる場合に合う。
- `next-transition` は 3 年先まで探す。
- 既定のゾーン (`system-zone`) は TZ 環境変数 → /etc/timezone → /etc/localtime → UTC の順。`now-instant` は Java と同じくマイクロ秒に丸める
  (`now-instant-ns` はナノ秒のまま。Java の Clock.systemUTC と同じ精度)。

## 理由

- Clay には日時とタイムゾーンが無い (docs/clay-capabilities.md)。実 Mule の DataWeave は java.time の上で動くので、その意味と文言に合わせる。

## 場所

- `mulay.lib.time.types`、`mulay.lib.time.civil`、`mulay.lib.time.local`、`mulay.lib.time.zoned/zdt-of-local`、`zdt-until`
- `mulay.lib.time.fmt/compile`、`parse`、`with-resolver`、`parse-number`、`mulay.lib.time.locales`、`mulay.lib.time.names`
- `mulay.lib.time.tz/rules-for-id`、`parse-tzif`、`parse-posix`、`dst-at?`、`std-offset-at`、`next-transition`、`system-zone`、`now-instant`、
  `now-instant-ns`
