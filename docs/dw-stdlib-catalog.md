# DataWeave 2.x 標準ライブラリ関数カタログ

一次資料は実 Mule 4.11.3 同梱の DataWeave 2.11.2 の `.dwl` ソース
(`services/mule-service-weave-ee-2.11.2/lib/wlang-2.11.2.jar` の `dw/**/*.dwl` と、`mule-service-weave-2.11.2.jar` の `Mule.dwl`)。
シグネチャはソースの `fun` 宣言をそのまま (空白だけ詰めて) 写した。
`core-modules-2.11.2.jar` には同じモジュールがコンパイル済み (`.bdwl`) で入っている。

列の意味:

- **導入**: `@Since(version=...)` 注釈 (無ければ doc コメントの "Introduced in DataWeave x.y")。空欄は注記なし (2.0 以前からある)。
- **状態**: `非推奨` は `@Deprecated`、`実験的` は `@Experimental`、`内部` は `@Internal` (利用者のスクリプトからは呼べない。実 DW は "can not be access from `anonymous`" で失敗する)。
- **例**: `test/fixtures/dw/docs/<モジュール>/<関数>-<n>.dwt` の件数 (関数名単位。オーバーロードごとには数えていない)。期待値は実 DW 2.11.2 で生成済み。
  言語ガイド・形式・cookbook 由来の例 (`guide/`、`formats/`、`cookbook/`) は関数ごとには数えていない。

演算子のうち `++` と `--` は `dw::Core` の関数として定義されている。それ以外の演算子 (`+`、`-`、`as`、`is`、`default`、`update`、`match`、`do`、`if`、`and`/`or`、比較、セレクタ) は言語組み込みで、`guide/dw-operators-*`、`guide/selectors-*`、`guide/pattern-matching-*`、`guide/flow-control-*` に例がある。

## 概要

| モジュール | 関数 (名前) | オーバーロード | 例のある関数 | 被覆率 |
|---|---:|---:|---:|---:|
| `dw::Core` | 80 | 158 | 78 | 97% |
| `dw::Crypto` | 5 | 5 | 5 | 100% |
| `dw::Runtime` | 17 | 17 | 17 | 100% |
| `dw::System` | 2 | 2 | 2 | 100% |
| `dw::core::Arrays` | 19 | 34 | 19 | 100% |
| `dw::core::Binaries` | 7 | 9 | 7 | 100% |
| `dw::core::Dates` | 13 | 23 | 13 | 100% |
| `dw::core::Numbers` | 6 | 10 | 6 | 100% |
| `dw::core::Objects` | 9 | 13 | 9 | 100% |
| `dw::core::Periods` | 9 | 9 | 9 | 100% |
| `dw::core::Strings` | 47 | 93 | 47 | 100% |
| `dw::core::Types` | 37 | 37 | 37 | 100% |
| `dw::core::URL` | 6 | 6 | 6 | 100% |
| `dw::module::Mime` | 3 | 3 | 3 | 100% |
| `dw::module::Multipart` | 4 | 6 | 4 | 100% |
| `dw::util::Coercions` | 20 | 33 | 20 | 100% |
| `dw::util::Diff` | 1 | 1 | 1 | 100% |
| `dw::util::Math` | 17 | 17 | 17 | 100% |
| `dw::util::Timer` | 4 | 4 | 4 | 100% |
| `dw::util::Tree` | 9 | 9 | 9 | 100% |
| `dw::util::Values` | 5 | 14 | 5 | 100% |
| `dw::xml::Dtd` | 1 | 1 | 1 | 100% |
| `dw::Mule` | 3 | 3 | 0 | 0% |
| **合計** | **324** | **507** | **319** | **98.4%** |

`@Internal` を除いた公開関数では 317/320 (99.0%)。
例の無い関数: `dw::Core` の `native` / `logInternal` (内部)、`dw::Mule` の `lookup` / `p` / `causedBy` (Mule の実行文脈が要り、単体の DW では `BindingContext was not bind as a Service` で失敗するため golden にできない)。
`dw::Mule` のモジュール名はソース上 `Mule` (jar 直下の `Mule.dwl`) で、Mule の中では `Mule::p(...)` または自動 import で呼ぶ。ドキュメントの表記に合わせて `dw::Mule` と書いた。

## dw::Core

doc: https://docs.mulesoft.com/dataweave/2.11/dw-core

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `evaluateCompatibilityFlag` | `evaluateCompatibilityFlag(flag: String): Boolean` | 2.5.0 |  | 1 |
| `isDefaultOperatorDisabledExceptionHandling` | `isDefaultOperatorDisabledExceptionHandling(): Boolean` | 2.5.0 | 内部 | 1 |
| `isLegacySizeOfNumber` | `isLegacySizeOfNumber(): Boolean` | 2.6.0 | 内部 | 1 |
| `logWith` | `logWith <T>(level: LogLevel, prefix: String, value: T): T` | 2.10.0 |  | 1 |
| `logDebug` | `logDebug <T>(prefix: String = "", value: T): T` | 2.10.0 |  | 1 |
| `logInfo` | `logInfo <T>(prefix: String = "", value: T): T` | 2.10.0 |  | 1 |
| `logWarn` | `logWarn <T>(prefix: String = "", value: T): T` | 2.10.0 |  | 1 |
| `logError` | `logError <T>(prefix: String = "", value: T): T` | 2.10.0 |  | 1 |
| `logInternal` | `logInternal <T>(context: Object, level: LogLevel, prefix: String, value: T): T` | 2.10.0 | 内部 | 0 |
| `log` | `log <T>(prefix: String = "", value: T): T` |  |  | 2 |
| `read` | `read(stringToParse: String \| Binary, contentType: String = "application/dw", readerProperties: Object = {}): Any` |  |  | 3 |
| `readUrl` | `readUrl(url: String, contentType: String = "application/dw", readerProperties: Object = {}): Any` |  |  | 1 |
| `write` | `write (value: Any, contentType: String = "application/dw", writerProperties: Object = {}): String \| Binary` |  |  | 2 |
| `random` | `random(): Number` |  |  | 1 |
| `randomInt` | `randomInt(upperBound: Number): Number` |  |  | 1 |
| `uuid` | `uuid(): String` |  |  | 1 |
| `now` | `now(): DateTime` |  |  | 2 |
| `native` | `native(identifier: String): Nothing` |  | 内部 | 0 |
| `xsiType` | `xsiType(name: String, namespace: Namespace)` | 2.2.2 |  | 1 |
| `++` | `++ <S,T>(source: Array<S>, with: Array<T>): Array<S \| T>` |  |  | 15 |
|  | `++(source: String, with: String): String` |  |  |  |
|  | `++<T <: {},Q <: {} >(source: T, with: Q): T & Q` |  |  |  |
|  | `++(date: Date, time: LocalTime): LocalDateTime` |  |  |  |
|  | `++(time: LocalTime, date: Date): LocalDateTime` |  |  |  |
|  | `++(date: Date, time: Time): DateTime` |  |  |  |
|  | `++(time: Time, date: Date): DateTime` |  |  |  |
|  | `++(date: Date, timezone: TimeZone): DateTime` |  |  |  |
|  | `++(timezone: TimeZone, date: Date): DateTime` |  |  |  |
|  | `++(dateTime: LocalDateTime, timezone: TimeZone): DateTime` |  |  |  |
|  | `++(timezone: TimeZone, datetime: LocalDateTime): DateTime` |  |  |  |
|  | `++ (time: LocalTime, timezone: TimeZone): Time` |  |  |  |
|  | `++ (timezone: TimeZone, time: LocalTime): Time` |  |  |  |
| `mapObject` | `mapObject <K,V>(@StreamCapable object: {(K)?: V}, mapper : (value: V, key: K, index: Number) -> Object): Object` |  |  | 2 |
|  | `mapObject(value: Null, mapper : (value: Nothing, key: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `pluck` | `pluck <K,V,R>(@StreamCapable object: {(K)?: V}, mapper: (value: V, key: K, index: Number) -> R): Array<R>` |  |  | 2 |
|  | `pluck(value: Null, mapper:(value: Nothing, key: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `zip` | `zip<T,R>(left: Array<T>, right: Array<R>): Array<Array<T \| R>>` |  |  | 3 |
| `map` | `map <T,R>(@StreamCapable items: Array<T>, mapper: (item: T, index: Number) -> R): Array<R>` |  |  | 4 |
|  | `map(@StreamCapable value: Null, mapper: (item: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `flatMap` | `flatMap<T,R>(@StreamCapable items: Array<T>, mapper:(item: T, index: Number) -> Array<R>): Array<R>` |  |  | 1 |
|  | `flatMap<T,R>(@StreamCapable value: Null, mapper: (item: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `filter` | `filter <T>(@StreamCapable items: Array<T>, criteria: (item: T, index: Number) -> Boolean): Array<T>` |  |  | 6 |
|  | `filter(@StreamCapable text: String, criteria: (character: String, index: Number) -> Boolean): String` |  |  |  |
|  | `filter(@StreamCapable value: Null, criteria: (item: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `filterObject` | `filterObject <K,V>(@StreamCapable value: {(K)?: V}, criteria: (value: V, key: K, index: Number) -> Boolean): {(K)?: V}` |  |  | 4 |
|  | `filterObject(value: Null, criteria: (value: Nothing, key: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `entriesOf` | `entriesOf<T <: Object>(obj: T): Array<{\|key: Key, value: Any, attributes: Object\|}>` | 2.3.0 |  | 1 |
|  | `entriesOf(obj: Null): Null` | 2.4.0 |  |  |
| `namesOf` | `namesOf(obj: Object): Array<String>` | 2.3.0 |  | 1 |
|  | `namesOf(obj: Null): Null` | 2.4.0 |  |  |
| `keysOf` | `keysOf<K,V>(obj: {(K)?: V}): Array<K>` | 2.3.0 |  | 2 |
|  | `keysOf(obj: Null): Null` | 2.4.0 |  |  |
| `valuesOf` | `valuesOf <K,V>(obj: {(K)?: V}): Array<V>` | 2.3.0 |  | 1 |
|  | `valuesOf (obj: Null): Null` | 2.4.0 |  |  |
| `replace` | `replace(text: String, matcher: Regex): ((Array<String>, Number) -> String) -> String` |  |  | 3 |
|  | `replace(text: String, matcher: String): ((Array<String>, Number) -> String) -> String` |  |  |  |
|  | `replace(text: Null, matcher: Any): ((Nothing, Nothing) -> Any) -> Null` | 2.4.0 |  |  |
| `with` | `with<V,U,R,X>(toBeReplaced: ((V, U) -> R) -> X, replacer: (V, U) -> R): X` |  |  | 1 |
| `reduce` | `reduce <T>(@StreamCapable items: Array<T>, callback: (item: T, accumulator: T) -> T): T \| Null` |  |  | 5 |
|  | `reduce <T,A>(@StreamCapable items: Array<T>, callback: (item: T, accumulator: A) -> A): A` |  |  |  |
|  | `reduce (@StreamCapable text: String, callback: (item: String, accumulator: String) -> String): String` |  |  |  |
|  | `reduce <A>(@StreamCapable text: String, callback: (item: String, accumulator: A) -> A): A` |  |  |  |
|  | `reduce <T, A>(@StreamCapable items: Null, callback: (item: T, accumulator: A) -> A): Null` |  |  |  |
| `groupBy` | `groupBy <T,R>(items: Array<T>, criteria: (item: T, index: Number) -> R): {\|(R): Array<T>\|}` |  |  | 6 |
|  | `groupBy <R>(text: String, criteria: (character: String, index: Number) -> R): {(R): String}` |  |  |  |
|  | `groupBy <K,V,R>(object: {(K)?: V}, criteria: (value: V, key: K) -> R): {(R): {(K)?: V}}` |  |  |  |
|  | `groupBy(value: Null, criteria: (Nothing, Nothing) -> Any): Null` |  |  |  |
| `--` | `-- <S>(source: Array<S>, toRemove: Array<Any>): Array<S>` |  |  | 4 |
|  | `-- <K,V>(source: {(K)?: V}, toRemove: Object): {(K)?:V}` |  |  |  |
|  | `--(source: Object, keys: Array<String>)` |  |  |  |
|  | `--(source: Object, keys: Array<Key>)` |  |  |  |
|  | `--(source: Null, keys: Any)` | 2.4.0 |  |  |
| `find` | `find <T>(@StreamCapable() elements: Array<T>, elementToFind: Any): Array<Number>` |  |  | 3 |
|  | `find(@StreamCapable() text: String, matcher: Regex): Array<Array<Number>>` |  |  |  |
|  | `find(@StreamCapable() text: String, textToFind: String): Array<Number>` |  |  |  |
|  | `find(@StreamCapable() text: Null, textToFind: Any): Array<Nothing>` |  |  |  |
| `distinctBy` | `distinctBy <T>(@StreamCapable items: Array<T>, criteria: (item: T, index: Number) -> Any): Array<T>` |  |  | 4 |
|  | `distinctBy <K, V>(object: {(K)?: V}, criteria: (value: V, key: K) -> Any): Object` |  |  |  |
|  | `distinctBy(@StreamCapable items: Null, criteria: (item: Nothing, index: Nothing) -> Any): Null` |  |  |  |
| `to` | `to(from: Number, to: Number): Range` |  |  | 2 |
| `contains` | `contains <T>(@StreamCapable items: Array<T>, element: Any): Boolean` |  |  | 6 |
|  | `contains(text: String, toSearch: String): Boolean` |  |  |  |
|  | `contains(text: String, matcher: Regex): Boolean` |  |  |  |
|  | `contains(text: Null, matcher: Any): false` | 2.4.0 |  |  |
| `orderBy` | `orderBy <K,V,R, O <: {(K)?: V}>(object: O, criteria: (value: V, key: K) -> R): O` |  |  | 6 |
|  | `orderBy <T,R>(array: Array<T>, criteria: (item: T, index: Number) -> R): Array<T>` |  |  |  |
|  | `orderBy(value: Null, criteria: (item: Nothing, index: Nothing) -> Null): Null` |  |  |  |
| `avg` | `avg(values: Array<Number>): Number` |  |  | 1 |
| `max` | `max <T <: Comparable>(@StreamCapable values: Array<T>): T \| Null` |  |  | 1 |
| `min` | `min <T <: Comparable>(@StreamCapable values: Array<T>): T \| Null` |  |  | 1 |
| `sum` | `sum(@StreamCapable values: Array<Number>): Number` |  |  | 1 |
| `sizeOf` | `sizeOf(array: Array<Any>): Number` |  |  | 12 |
|  | `sizeOf(object: Object): Number` |  |  |  |
|  | `sizeOf(binary: Binary): Number` |  |  |  |
|  | `sizeOf(text: String): Number` |  |  |  |
|  | `sizeOf(value: Period): Number` | 2.6.0 |  |  |
|  | `sizeOf(value: DateTime): Number` | 2.6.0 |  |  |
|  | `sizeOf(value: LocalDateTime): Number` | 2.6.0 |  |  |
|  | `sizeOf(number: Number): Number` | 2.6.0 |  |  |
|  | `sizeOf(n: Null): Null` | 2.4.0 |  |  |
| `flatten` | `flatten <T, Q>(@StreamCapable items: Array<Array<T> \| Q>): Array<T \| Q>` |  |  | 2 |
|  | `flatten (@StreamCapable value: Null): Null` |  |  |  |
| `unzip` | `unzip<T>(items: Array<Array<T>>):Array<Array<T>>` |  |  | 3 |
| `endsWith` | `endsWith(text: String, suffix: String): Boolean` |  |  | 1 |
|  | `endsWith(text: Null, suffix: Any): false` | 2.4.0 |  |  |
| `joinBy` | `joinBy(@StreamCapable elements: Array<StringCoerceable>, separator: String): String` |  |  | 1 |
|  | `joinBy(n: Null, separator: Any): Null` | 2.4.0 |  |  |
| `scan` | `scan(text: String, matcher: Regex): Array<Array<String>>` |  |  | 2 |
|  | `scan(text: Null, matcher: Any): Null` | 2.4.0 |  |  |
| `splitBy` | `splitBy(text: String, regex: Regex): Array<String>` |  |  | 6 |
|  | `splitBy(text: String, separator: String): Array<String>` |  |  |  |
|  | `splitBy(text: Null, separator: Any)` | 2.4.0 |  |  |
| `startsWith` | `startsWith(text: String, prefix: String): Boolean` |  |  | 1 |
|  | `startsWith(text: Null, prefix: Any): false` | 2.4.0 |  |  |
| `matches` | `matches(text: String, matcher: Regex): Boolean` |  |  | 1 |
|  | `matches(text: Null, matcher: Any): false` | 2.4.0 |  |  |
| `match` | `match(text: String, matcher: Regex): Array<String>` |  |  | 2 |
|  | `match(text: Null, matcher: Any) : Null` | 2.4.0 |  |  |
| `lower` | `lower(text: String): String` |  |  | 1 |
|  | `lower(value:Null) : Null` |  |  |  |
| `trim` | `trim(text: String): String` |  |  | 2 |
|  | `trim(value: Null): Null` |  |  |  |
| `upper` | `upper(text: String): String` |  |  | 1 |
|  | `upper(value: Null): Null` |  |  |  |
| `pow` | `pow(base: Number, power: Number): Number` |  |  | 1 |
| `mod` | `mod(dividend: Number, divisor: Number): Number` |  |  | 1 |
| `sqrt` | `sqrt(number: Number): Number` |  |  | 1 |
| `abs` | `abs(number: Number): Number` |  |  | 1 |
| `ceil` | `ceil(number: Number): Number` |  |  | 1 |
| `floor` | `floor(number: Number): Number` |  |  | 1 |
| `typeOf` | `typeOf <T>(value: T): Type<T>` |  |  | 2 |
| `round` | `round(number: Number): Number` |  |  | 1 |
| `isEmpty` | `isEmpty(elements: Array<Any>): Boolean` |  |  | 5 |
|  | `isEmpty(value: String): Boolean` |  |  |  |
|  | `isEmpty(value: Object): Boolean` |  |  |  |
|  | `isEmpty(value: Binary): Boolean` | 2.11.0 |  |  |
|  | `isEmpty(value: Null): true` |  |  |  |
| `isLeapYear` | `isLeapYear(dateTime: DateTime): Boolean` |  |  | 3 |
|  | `isLeapYear(date: Date): Boolean` |  |  |  |
|  | `isLeapYear(datetime: LocalDateTime): Boolean` |  |  |  |
| `isDecimal` | `isDecimal(number: Number): Boolean` |  |  | 1 |
| `isInteger` | `isInteger(number: Number): Boolean` |  |  | 1 |
| `isBlank` | `isBlank(text: String \| Null): Boolean` |  |  | 1 |
| `isOdd` | `isOdd(number: Number): Boolean` |  |  | 1 |
| `isEven` | `isEven(number: Number): Boolean` |  |  | 1 |
| `minBy` | `minBy<T>(@StreamCapable array: Array<T>, criteria: (item: T) -> Comparable): T \| Null` |  |  | 2 |
| `maxBy` | `maxBy<T>(@StreamCapable array: Array<T>, criteria: (item: T) -> Comparable): T \| Null` |  |  | 3 |
| `daysBetween` | `daysBetween(from: Date, to: Date): Number` |  |  | 1 |
| `indexOf` | `indexOf(array: Array, value: Any): Number` | 2.4.0 |  | 2 |
|  | `indexOf(theString: String, search: String): Number` | 2.4.0 |  |  |
|  | `indexOf(array: Null, value: Any): Number` | 2.4.0 |  |  |
| `lastIndexOf` | `lastIndexOf(array: Array, value: Any): Number` | 2.4.0 |  | 2 |
|  | `lastIndexOf(array: String, value: String): Number` | 2.4.0 |  |  |
|  | `lastIndexOf(array: Null, value: Any): Number` | 2.4.0 |  |  |
| `then` | `then(value: Null, callback: (previousResult: Nothing) -> Any): Null` | 2.4.0 |  | 1 |
|  | `then<T, R>(previous: T, callback: (result: T) -> R): R` | 2.4.0 |  |  |
| `onNull` | `onNull<R>(previous: Null, callback:() -> R): R` | 2.4.0 |  | 1 |
|  | `onNull<T>(previous: T, callback:() -> Any): T` | 2.4.0 |  |  |

## dw::Crypto

doc: https://docs.mulesoft.com/dataweave/2.11/dw-crypto

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `HMACBinary` | `HMACBinary(secret: Binary, content: Binary, algorithm: String = "HmacSHA1"): Binary` |  |  | 1 |
| `hashWith` | `hashWith(content: Binary, algorithm: String = "SHA-1"): Binary` |  |  | 1 |
| `HMACWith` | `HMACWith(secret: Binary, content: Binary, @Since(version = "2.2.0") algorithm: String = "HmacSHA1"): String` | 2.2.0 |  | 1 |
| `MD5` | `MD5(content: Binary): String` |  |  | 1 |
| `SHA1` | `SHA1(content: Binary): String` |  |  | 1 |

## dw::Runtime

doc: https://docs.mulesoft.com/dataweave/2.11/dw-runtime

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `fail` | `fail (message: String = 'Error'): Nothing` |  |  | 1 |
| `failIf` | `failIf <T>(value: T, evaluator: (value: T) -> Boolean, message: String = 'Failed'): T` |  |  | 2 |
| `run` | `run(fileToExecute: String, fs: Dictionary<String>, readerInputs: Dictionary<ReaderInput> = {}, inputValues: Dictionary<Any> = {}, configuration: RuntimeExecutionConfiguration = {}): RunResult` |  | 実験的 | 1 |
| `eval` | `eval(fileToExecute: String, fs: Dictionary<String>, readerInputs: Dictionary<ReaderInput> = {}, inputValues: Dictionary<Any> = {}, configuration: RuntimeExecutionConfiguration = {}): EvalResult` |  | 実験的 | 1 |
| `runUrl` | `runUrl(url: String, readerInputs: Dictionary<ReaderInput> = {}, inputValues: Dictionary<Any> = {}, configuration: RuntimeExecutionConfiguration = {}): RunResult` |  | 実験的 | 1 |
| `evalUrl` | `evalUrl(url: String, readerInputs: Dictionary<ReaderInput> = {}, inputValues: Dictionary<Any> = {}, configuration: RuntimeExecutionConfiguration = {}): EvalResult` |  | 実験的 | 1 |
| `dataFormatsDescriptor` | `dataFormatsDescriptor(): Array<DataFormatDescriptor>` |  | 実験的 | 1 |
| `wait` | `wait <T>(value: T, timeout: Number): T` |  |  | 1 |
| `try` | `try<T>(delegate: () -> T): TryResult<T>` |  |  | 1 |
| `orElseTry` | `orElseTry<T, R>(previous: TryResult<T>, orElse: () -> R): TryResult<T \| R>` | 2.2.0 |  | 1 |
| `orElse` | `orElse<T, E, R>(previous: Result<T, E>, orElse: () -> R): T \| R` | 2.2.0 |  | 1 |
| `locationString` | `locationString(value:Any): String` |  |  | 1 |
| `location` | `location(value: Any): Location` | 2.4.0 |  | 1 |
| `props` | `props(): Dictionary<String>` |  |  | 1 |
| `prop` | `prop(propertyName: String): String \| Null` |  |  | 1 |
| `version` | `version(): String` | 2.5.0 |  | 1 |
| `findDataFormatDescriptorByMime` | `findDataFormatDescriptorByMime(mime: dw::module::Mime::MimeType): DataFormatDescriptor \| Null` | 2.7.0 | 実験的 | 1 |

## dw::System

doc: https://docs.mulesoft.com/dataweave/2.11/dw-system

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `envVars` | `envVars(): Dictionary<String>` |  |  | 1 |
| `envVar` | `envVar(variableName: String): String \| Null` |  |  | 1 |

## dw::core::Arrays

doc: https://docs.mulesoft.com/dataweave/2.11/dw-arrays

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `some` | `some<T>(list: Array<T>, condition: (T) -> Boolean): Boolean` |  |  | 1 |
|  | `some(list: Null, condition: (Nothing) -> Any): Boolean` | 2.3.0 |  |  |
| `every` | `every<T>(list: Array<T>, condition: (T) -> Boolean): Boolean` |  |  | 1 |
|  | `every(value: Null, condition: (Nothing) -> Any): Boolean` | 2.3.0 |  |  |
| `countBy` | `countBy<T>(@StreamCapable array: Array<T>, matchingFunction: (T) -> Boolean): Number` |  |  | 1 |
|  | `countBy(array: Null, matchingFunction: (Nothing) -> Any): Null` | 2.4.0 |  |  |
| `sumBy` | `sumBy<T>(@StreamCapable array: Array<T>, numberSelector: (T) -> Number): Number` |  |  | 1 |
|  | `sumBy(array: Null, numberSelector: (Nothing) -> Any): Null` | 2.4.0 |  |  |
| `divideBy` | `divideBy<T>(items: Array<T>, amount: Number): Array<Array<T>>` |  |  | 1 |
|  | `divideBy(items: Null, amount: Any): Null` | 2.4.0 |  |  |
| `join` | `join<L <: {}, R <: {}>(left:Array<L>, right:Array<R>, leftCriteria: (leftValue: L) -> String, rightCriteria: (rightValue: R) -> String): Array<Pair<L, R>>` | 2.2.0 |  | 1 |
| `leftJoin` | `leftJoin<L <: {}, R <: {}>(left:Array<L>, right:Array<R>, leftCriteria: (leftValue: L) -> String, rightCriteria: (rightValue: R) -> String): Array<{l: L,r?: R}>` | 2.2.0 |  | 1 |
| `outerJoin` | `outerJoin<L <: {}, R <: {}>(left:Array<L>, right:Array<R>, leftCriteria: (leftValue: L) -> String, rightCriteria: (rightValue: R) -> String): Array<{l?: L,r?: R}>` | 2.2.0 |  | 1 |
| `take` | `take<T>(array: Array<T>, n: Number): Array<T>` | 2.2.0 |  | 1 |
|  | `take(array: Null, n: Any): Null` | 2.4.0 |  |  |
| `drop` | `drop<T>(array: Array<T>, n: Number): Array<T>` | 2.2.0 |  | 1 |
|  | `drop(array: Null, n: Any): Null` | 2.4.0 |  |  |
| `slice` | `slice<T>(array: Array<T>, from: Number, until: Number): Array<T>` | 2.2.0 |  | 1 |
|  | `slice(array: Null, from: Any, until: Any): Null` | 2.4.0 |  |  |
| `indexOf` | `indexOf<T>(array: Array<T>, toFind: T): Number` | 2.2.0 |  | 1 |
| `indexWhere` | `indexWhere<T>(array: Array<T>, condition: (item: T) -> Boolean): Number` | 2.2.0 |  | 1 |
|  | `indexWhere(array: Null, condition: (item: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `splitAt` | `splitAt<T>(array: Array<T>, n: Number): Pair<Array<T>, Array<T>>` | 2.2.0 |  | 1 |
|  | `splitAt(array: Null, n: Any): Null` | 2.4.0 |  |  |
| `takeWhile` | `takeWhile<T>(array: Array<T>, condition: (item: T) -> Boolean): Array<T>` | 2.2.0 |  | 1 |
|  | `takeWhile(array: Null, condition: (item: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `dropWhile` | `dropWhile<T>(array: Array<T>, condition: (item: T) -> Boolean): Array<T>` | 2.2.0 |  | 1 |
|  | `dropWhile(array: Null, condition: (item: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `splitWhere` | `splitWhere<T>(array: Array<T>, condition: (item: T) -> Boolean): Pair<Array<T>, Array<T>>` | 2.2.0 |  | 1 |
|  | `splitWhere(array: Null, condition: (item: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `partition` | `partition<T>(array: Array<T>, condition: (item: T) -> Boolean): {success: Array<T>, failure: Array<T>}` | 2.2.0 |  | 1 |
|  | `partition(array: Null, condition: (item: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `firstWith` | `firstWith<T>(array:Array<T>, condition: (item: T, index: Number) -> Boolean): T \| Null` | 2.3.0 |  | 1 |
|  | `firstWith(array: Null, condition: (item: Nothing, index: Nothing) -> Any): Null` | 2.4.0 |  |  |

## dw::core::Binaries

doc: https://docs.mulesoft.com/dataweave/2.11/dw-binaries

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `toHex` | `toHex(content: Binary): String` |  |  | 1 |
| `fromHex` | `fromHex(hexString: String): Binary` |  |  | 1 |
| `toBase64` | `toBase64(content: Binary): String` |  |  | 1 |
| `fromBase64` | `fromBase64(base64String: String): Binary` |  |  | 1 |
| `readLinesWith` | `readLinesWith(content: Binary, charset: String): Array<String>` | 2.2.0 |  | 1 |
| `writeLinesWith` | `writeLinesWith(content: Array<String>, charset: String): Binary` | 2.2.0 |  | 1 |
| `concatWith` | `concatWith(source: Binary, with: Binary): Binary` | 2.5.0 |  | 1 |
|  | `concatWith(source: Binary, with: Null): Binary` |  |  |  |
|  | `concatWith(source: Null, with: Binary): Binary` |  |  |  |

## dw::core::Dates

doc: https://docs.mulesoft.com/dataweave/2.11/dw-dates

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `today` | `today(): Date` | 2.4.0 |  | 1 |
| `yesterday` | `yesterday(): Date` | 2.4.0 |  | 1 |
| `tomorrow` | `tomorrow(): Date` | 2.4.0 |  | 1 |
| `date` | `date(parts: DateFactory): Date` | 2.4.0 |  | 1 |
| `dateTime` | `dateTime(parts: DateTimeFactory): DateTime` | 2.4.0 |  | 1 |
| `localDateTime` | `localDateTime(parts: LocalDateTimeFactory): LocalDateTime` | 2.4.0 |  | 1 |
| `localTime` | `localTime(parts: LocalTimeFactory): LocalTime` | 2.4.0 |  | 1 |
| `time` | `time(parts: TimeFactory): Time` | 2.4.0 |  | 1 |
| `atBeginningOfHour` | `atBeginningOfHour(dateTime: DateTime): DateTime` | 2.4.0 |  | 4 |
|  | `atBeginningOfHour(localDateTime: LocalDateTime): LocalDateTime` | 2.4.0 |  |  |
|  | `atBeginningOfHour(localTime: LocalTime): LocalTime` | 2.4.0 |  |  |
|  | `atBeginningOfHour(time: Time): Time` | 2.4.0 |  |  |
| `atBeginningOfDay` | `atBeginningOfDay(dateTime: DateTime): DateTime` | 2.4.0 |  | 2 |
|  | `atBeginningOfDay(localDateTime: LocalDateTime): LocalDateTime` | 2.4.0 |  |  |
| `atBeginningOfMonth` | `atBeginningOfMonth(dateTime: DateTime): DateTime` | 2.4.0 |  | 3 |
|  | `atBeginningOfMonth(localDateTime: LocalDateTime): LocalDateTime` | 2.4.0 |  |  |
|  | `atBeginningOfMonth(date: Date): Date` | 2.4.0 |  |  |
| `atBeginningOfWeek` | `atBeginningOfWeek(dateTime: DateTime): DateTime` | 2.4.0 |  | 3 |
|  | `atBeginningOfWeek(localDateTime: LocalDateTime): LocalDateTime` | 2.4.0 |  |  |
|  | `atBeginningOfWeek(date: Date): Date` | 2.4.0 |  |  |
| `atBeginningOfYear` | `atBeginningOfYear(dateTime: DateTime): DateTime` | 2.4.0 |  | 3 |
|  | `atBeginningOfYear(localDateTime: LocalDateTime): LocalDateTime` | 2.4.0 |  |  |
|  | `atBeginningOfYear(date: Date): Date` | 2.4.0 |  |  |

## dw::core::Numbers

doc: https://docs.mulesoft.com/dataweave/2.11/dw-numbers

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `toHex` | `toHex(number: Number): String` | 2.2.0 |  | 1 |
|  | `toHex(number: Null): Null` | 2.2.0 |  |  |
| `toBinary` | `toBinary(number: Number): String` | 2.2.0 |  | 1 |
|  | `toBinary(number: Null): Null` | 2.2.0 |  |  |
| `fromHex` | `fromHex(hexText: String): Number` | 2.2.0 |  | 1 |
|  | `fromHex(hexText: Null): Null` | 2.2.0 |  |  |
| `fromBinary` | `fromBinary(binaryText: String): Number` | 2.2.0 |  | 1 |
|  | `fromBinary(binaryText: Null): Null` | 2.2.0 |  |  |
| `fromRadixNumber` | `fromRadixNumber(numberStr: String, radix: Number): Number` | 2.2.0 |  | 1 |
| `toRadixNumber` | `toRadixNumber(number: Number, radix: Number): String` | 2.2.0 |  | 1 |

## dw::core::Objects

doc: https://docs.mulesoft.com/dataweave/2.11/dw-objects

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `entrySet` | `entrySet<T <: Object>(obj: T): Array<{\|key: Key, value: Any, attributes: Object\|}>` |  | 非推奨 (2.3.0〜, 代替 `dw::Core::entriesOf`) | 1 |
| `nameSet` | `nameSet(obj: Object): Array<String>` |  | 非推奨 (2.3.0〜, 代替 `dw::Core::namesOf`) | 1 |
| `keySet` | `keySet<K,V>(obj: {(K)?: V}): Array<K>` |  | 非推奨 (2.3.0〜, 代替 `dw::Core::keysOf`) | 2 |
| `valueSet` | `valueSet <K,V>(obj: {(K)?: V}): Array<V>` |  | 非推奨 (2.3.0〜, 代替 `dw::Core::valuesOf`) | 1 |
| `mergeWith` | `mergeWith<T <: Object,V <: Object>(source: T, target: V): ?` |  |  | 1 |
|  | `mergeWith<T <: Object>(a: Null, b: T): T` |  |  |  |
|  | `mergeWith<T <: Object>(a: T, b: Null): T` |  |  |  |
| `divideBy` | `divideBy(items: Object, amount: Number): Array<{}>` |  |  | 1 |
| `takeWhile` | `takeWhile<T>(obj: Object, condition: (value: Any, key: Key) -> Boolean): Object` | 2.3.0 |  | 1 |
| `everyEntry` | `everyEntry(object: Object, condition: (value: Any, key: Key) -> Boolean): Boolean` | 2.3.0 |  | 1 |
|  | `everyEntry(list: Null, condition: (Nothing, Nothing) -> Boolean): Boolean` | 2.3.0 |  |  |
| `someEntry` | `someEntry(obj: Object, condition: (value: Any, key: Key) -> Boolean): Boolean` | 2.3.0 |  | 1 |
|  | `someEntry(obj: Null, condition: (value: Nothing, key: Nothing) -> Boolean): Boolean` | 2.3.0 |  |  |

## dw::core::Periods

doc: https://docs.mulesoft.com/dataweave/2.11/dw-periods

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `between` | `between(endDateExclusive: Date, startDateInclusive: Date): Period` | 2.3.0 |  | 1 |
| `duration` | `duration(period: {days?: Number, hours?: Number, minutes?: Number, seconds?: Number }): Period` | 2.4.0 |  | 1 |
| `period` | `period(period: {years?: Number, months?: Number, days?: Number}): Period` | 2.4.0 |  | 1 |
| `years` | `years(nYears: Number):Period` | 2.4.0 |  | 1 |
| `months` | `months(nMonths: Number):Period` | 2.4.0 |  | 1 |
| `days` | `days(nDays: Number): Period` | 2.4.0 |  | 1 |
| `hours` | `hours(nHours: Number):Period` | 2.4.0 |  | 1 |
| `minutes` | `minutes(nMinutes: Number):Period` | 2.4.0 |  | 1 |
| `seconds` | `seconds(nSecs: Number):Period` | 2.4.0 |  | 1 |

## dw::core::Strings

doc: https://docs.mulesoft.com/dataweave/2.11/dw-strings

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `charCode` | `charCode(text: String): Number` |  |  | 1 |
|  | `charCode(text: Null): Null` | 2.4.0 |  |  |
| `charCodeAt` | `charCodeAt(content: String, position: Number): Number` |  |  | 1 |
|  | `charCodeAt(content: Null, position: Any): Null` | 2.4.0 |  |  |
| `fromCharCode` | `fromCharCode(charCode: Number): String` |  |  | 1 |
|  | `fromCharCode(charCode: Null): Null` | 2.4.0 |  |  |
| `pluralize` | `pluralize(text: String): String` |  |  | 1 |
|  | `pluralize(text: Null): Null` |  |  |  |
| `singularize` | `singularize(text: String): String` |  |  | 1 |
|  | `singularize(text: Null): Null` |  |  |  |
| `camelize` | `camelize(text: String): String` |  |  | 1 |
|  | `camelize(text: Null): Null` |  |  |  |
| `capitalize` | `capitalize(text: String): String` |  |  | 1 |
|  | `capitalize(text: Null): Null` |  |  |  |
| `ordinalize` | `ordinalize(num: Number): String` |  |  | 1 |
|  | `ordinalize(num: Null): Null` |  |  |  |
| `underscore` | `underscore(text: String): String` |  |  | 1 |
|  | `underscore(text: Null): Null` |  |  |  |
| `dasherize` | `dasherize(text: String): String` |  |  | 1 |
|  | `dasherize(text: Null): Null` |  |  |  |
| `leftPad` | `leftPad(text: String, size: Number, padText: String = " "): String` | 2.2.0 |  | 1 |
|  | `leftPad(text: Null, size: Any, padText: Any = " "): Null` | 2.2.0 |  |  |
| `rightPad` | `rightPad(text: String, size: Number, padChar: String = " "): String` | 2.2.0 |  | 1 |
|  | `rightPad(text: Null, size: Any, padText: Any = " "): Null` | 2.2.0 |  |  |
| `wrapWith` | `wrapWith(text: String, wrapper: String): String` | 2.2.0 |  | 1 |
|  | `wrapWith(text: Null, wrapper: Any): Null` | 2.2.0 |  |  |
| `wrapIfMissing` | `wrapIfMissing(text: String, wrapper: String): String` | 2.2.0 |  | 1 |
|  | `wrapIfMissing(text: Null, wrapper: String): Null` | 2.2.0 |  |  |
| `substringBefore` | `substringBefore(text: String, separator: String): String` | 2.2.0 |  | 1 |
|  | `substringBefore(text: Null, separator: String): Null` | 2.2.0 |  |  |
| `substringBeforeLast` | `substringBeforeLast(text: String, separator: String): String` | 2.2.0 |  | 1 |
|  | `substringBeforeLast(text: Null, separator: String): Null` | 2.2.0 |  |  |
| `substringAfter` | `substringAfter(text: String, separator: String): String` | 2.2.0 |  | 1 |
|  | `substringAfter(text: Null, separator: String): Null` | 2.2.0 |  |  |
| `substringAfterLast` | `substringAfterLast(text: String, separator: String): String` | 2.2.0 |  | 1 |
|  | `substringAfterLast(text: Null, separator: String): Null` | 2.2.0 |  |  |
| `repeat` | `repeat(text: String, times: Number): String` | 2.2.0 |  | 1 |
|  | `repeat(text: Null, times: Any): Null` | 2.4.0 |  |  |
| `unwrap` | `unwrap(text: String, wrapper: String): String` | 2.2.0 |  | 1 |
|  | `unwrap(text: Null, wrapper: String): Null` | 2.2.0 |  |  |
| `prependIfMissing` | `prependIfMissing(text: String, prefix: String): String` | 2.2.0 |  | 1 |
|  | `prependIfMissing(text: Null, prefix: String): Null` | 2.2.0 |  |  |
| `appendIfMissing` | `appendIfMissing(text:String, suffix: String): String` | 2.2.0 |  | 1 |
|  | `appendIfMissing(text: Null, suffix: String): Null` | 2.2.0 |  |  |
| `isNumeric` | `isNumeric(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isNumeric(text: Null): Boolean` | 2.2.0 |  |  |
| `isWhitespace` | `isWhitespace(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isWhitespace(text: Null): Boolean` | 2.2.0 |  |  |
| `isAlpha` | `isAlpha(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isAlpha(text: Null): Boolean` | 2.2.0 |  |  |
| `isAlphanumeric` | `isAlphanumeric(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isAlphanumeric(text: Null): Boolean` | 2.2.0 |  |  |
| `isUpperCase` | `isUpperCase(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isUpperCase(text: Null): Boolean` | 2.2.0 |  |  |
| `isLowerCase` | `isLowerCase(text: String): Boolean` | 2.2.0 |  | 1 |
|  | `isLowerCase(text: Null): Boolean` | 2.2.0 |  |  |
| `withMaxSize` | `withMaxSize(text: String, maxLength: Number): String` | 2.3.0 |  | 1 |
|  | `withMaxSize(text: Null, maxLength: Number): Null` | 2.3.0 |  |  |
| `replaceAll` | `replaceAll(text: String, target: String, replacement: String): String` | 2.4.0 |  | 1 |
|  | `replaceAll(text: Null, oldValue: String, newValue: String): Null` | 2.4.0 |  |  |
| `reverse` | `reverse(text: String): String` | 2.4.0 |  | 1 |
|  | `reverse(text: Null): Null` | 2.4.0 |  |  |
| `substring` | `substring(text: String, from: Number, until: Number): String` | 2.4.0 |  | 1 |
|  | `substring(text: Null, from: Any, until: Any): Null` | 2.4.0 |  |  |
| `substringEvery` | `substringEvery(text: String, amount: Number): Array<String>` | 2.4.0 |  | 1 |
|  | `substringEvery(text: Null, amount: Any): Null` | 2.4.0 |  |  |
| `substringBy` | `substringBy(text: String, predicate: (character: String, index: Number) -> Boolean): Array<String>` | 2.4.0 |  | 1 |
|  | `substringBy(text: Null, predicate: (character: Nothing, index: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `collapse` | `collapse(text: String): Array<String>` | 2.4.0 |  | 1 |
|  | `collapse(text: Null): Null` | 2.4.0 |  |  |
| `words` | `words(text:String): Array<String>` | 2.4.0 |  | 1 |
|  | `words(text:Null): Null` | 2.4.0 |  |  |
| `lines` | `lines(text:String): Array<String>` | 2.4.0 |  | 1 |
|  | `lines(text:Null): Null` | 2.4.0 |  |  |
| `first` | `first(text: String, amount: Number): String` | 2.4.0 |  | 1 |
|  | `first(text: Null, amount: Any): Null` | 2.4.0 |  |  |
| `last` | `last(text: String, amount: Number): String` | 2.4.0 |  | 1 |
|  | `last(text: Null, amount: Any): Null` | 2.4.0 |  |  |
| `countMatches` | `countMatches(text: String, pattern: String): Number` | 2.4.0 |  | 2 |
|  | `countMatches(text: String, pattern: Regex): Number` | 2.4.0 |  |  |
|  | `countMatches(text: Null, pattern: Any): Null` | 2.4.0 |  |  |
| `countCharactersBy` | `countCharactersBy(text: String, predicate: (character: String) -> Boolean): Number` | 2.4.0 |  | 1 |
|  | `countCharactersBy(text: Null, predicate: (character: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `everyCharacter` | `everyCharacter(text: String, condition: (character: String) -> Boolean): Boolean` | 2.4.0 |  | 1 |
|  | `everyCharacter(text: Null, condition: (character: Nothing) -> Any): true` | 2.4.0 |  |  |
| `someCharacter` | `someCharacter(text: String, condition: (character: String) -> Boolean): Boolean` | 2.4.0 |  | 1 |
|  | `someCharacter(text: Null, condition: (character: Nothing) -> Any): false` | 2.4.0 |  |  |
| `remove` | `remove(text: String, toRemove: String) : String` | 2.4.0 |  | 1 |
|  | `remove(text: Null, toRemove: Any) : Null` | 2.4.0 |  |  |
| `mapString` | `mapString(@StreamCapable text: String, mapper: (character: String, index: Number) -> String): String` | 2.4.0 |  | 1 |
|  | `mapString(@StreamCapable text: Null, mapper: (character: Nothing, index: Nothing) -> Any): Null` | 2.4.0 |  |  |
| `hammingDistance` | `hammingDistance(a: String, b: String): Number \| Null` | 2.4.0 |  | 1 |
| `levenshteinDistance` | `levenshteinDistance(a: String, b: String): Number` | 2.4.0 |  | 1 |

## dw::core::Types

doc: https://docs.mulesoft.com/dataweave/2.11/dw-types

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `isBooleanType` | `isBooleanType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isNumberType` | `isNumberType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isDateType` | `isDateType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isDateTimeType` | `isDateTimeType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isLocalDateTimeType` | `isLocalDateTimeType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isTimeType` | `isTimeType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isLocalTimeType` | `isLocalTimeType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isTimeZoneType` | `isTimeZoneType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isUriType` | `isUriType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isNamespaceType` | `isNamespaceType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isRangeType` | `isRangeType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isPeriodType` | `isPeriodType(t:Type) : Boolean` | 2.3.0 |  | 1 |
| `isBinaryType` | `isBinaryType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isNullType` | `isNullType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isNothingType` | `isNothingType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isAnyType` | `isAnyType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isTypeType` | `isTypeType(t:Type) : Boolean` | 2.3.0 |  | 1 |
| `isStringType` | `isStringType(t:Type) : Boolean` | 2.3.0 |  | 1 |
| `isRegexType` | `isRegexType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isKeyType` | `isKeyType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isLiteralType` | `isLiteralType(t: Type):Boolean` | 2.3.0 |  | 1 |
| `isFunctionType` | `isFunctionType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `literalValueOf` | `literalValueOf(t:Type): String \| Number \| Boolean` | 2.3.0 |  | 1 |
| `isObjectType` | `isObjectType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isArrayType` | `isArrayType(t:Type) : Boolean` | 2.3.0 |  | 1 |
| `isUnionType` | `isUnionType(t:Type): Boolean` | 2.3.0 |  | 1 |
| `isIntersectionType` | `isIntersectionType(t:Type):Boolean` | 2.3.0 |  | 1 |
| `unionItems` | `unionItems(t:Type): Array<Type>` | 2.3.0 |  | 1 |
| `isReferenceType` | `isReferenceType(t: Type):Boolean` | 2.3.0 |  | 1 |
| `nameOf` | `nameOf(t: Type): String` | 2.3.0 |  | 1 |
| `intersectionItems` | `intersectionItems(t:Type): Array<Type>` | 2.3.0 |  | 1 |
| `arrayItem` | `arrayItem(t: Type): Type` | 2.3.0 |  | 1 |
| `baseTypeOf` | `baseTypeOf(t:Type): Type` | 2.3.0 |  | 1 |
| `metadataOf` | `metadataOf(t:Type) : {}` | 2.3.0 |  | 1 |
| `functionParamTypes` | `functionParamTypes(t: Type): Array<FunctionParam>` | 2.3.0 |  | 1 |
| `functionReturnType` | `functionReturnType(t: Type): Type \| Null` | 2.3.0 |  | 1 |
| `objectFields` | `objectFields(t: Type): Array<Field>` | 2.3.0 |  | 1 |

## dw::core::URL

doc: https://docs.mulesoft.com/dataweave/2.11/dw-url

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `encodeURI` | `encodeURI(text: String): String` |  |  | 1 |
| `decodeURI` | `decodeURI(text: String): String` |  |  | 1 |
| `encodeURIComponent` | `encodeURIComponent(text: String): String` |  |  | 1 |
| `decodeURIComponent` | `decodeURIComponent(text: String): String` |  |  | 1 |
| `parseURI` | `parseURI(uri: String): URI` |  |  | 1 |
| `compose` | `compose(parts: Array<String>, interpolation: Array<String>): String` |  |  | 2 |

## dw::module::Mime

doc: https://docs.mulesoft.com/dataweave/2.11/dw-mime

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `fromString` | `fromString(mimeType: String): Result<MimeType, MimeTypeError>` | 2.7.0 |  | 3 |
| `toString` | `toString(mimeType: MimeType): String` | 2.7.0 |  | 2 |
| `isHandledBy` | `isHandledBy(base: MimeType, other: MimeType): Boolean` | 2.7.0 |  | 1 |

## dw::module::Multipart

doc: https://docs.mulesoft.com/dataweave/2.11/dw-multipart

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `field` | `field(opts: {\|name: String, value: Any, mime?: String, fileName?: String \|}): MultipartPart` |  |  | 3 |
|  | `field(name: String, value: Any, mime: String = "", fileName: String = ""): MultipartPart` |  |  |  |
| `file` | `file(opts: {\| name: String, path: String, mime?: String, fileName?: String \|})` |  |  | 1 |
|  | `file(fieldName: String, path: String, mime: String = 'application/octet-stream', sentFileName: String = 'filename')` |  |  |  |
| `form` | `form(parts: Array<MultipartPart>): Multipart` |  |  | 1 |
| `generateBoundary` | `generateBoundary(len: Number = 70): String` |  |  | 1 |

## dw::util::Coercions

doc: https://docs.mulesoft.com/dataweave/2.11/dw-coercions

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `toString` | `toString(number: Number, format: String \| Null = null, locale: String \| Null = null, roundMode: RoundingMode \| Null = null): String` | 2.4.0 |  | 5 |
|  | `toString(date: Date \| DateTime \| LocalDateTime \| LocalTime \| Time, format: String \| Null = null, locale: String \| Null = null): String` | 2.4.0 |  |  |
|  | `toString(binary: Binary, encoding: String): String` | 2.4.0 |  |  |
|  | `toString(data: TimeZone \| Uri \| Boolean\| Period\| Regex\| Key): String` | 2.4.0 |  |  |
|  | `toString(arr: Array<String>): String` | 2.4.0 |  |  |
| `toArray` | `toArray(@StreamCapable text: String): Array<String>` | 2.4.0 |  | 1 |
| `toNumber` | `toNumber(str: String, formatters: Array<Formatter>): Number` | 2.5.0 |  | 4 |
|  | `toNumber(dateTime: DateTime, unit: MillisOrSecs \| Null = null): Number` | 2.4.0 |  |  |
|  | `toNumber(period: Period, unit: PeriodUnits \| Null = null): Number` | 2.4.0 |  |  |
|  | `toNumber(value: String \| Key, format: String \| Null = null, locale: String \| Null = null): Number` | 2.4.0 |  |  |
| `toNumberOrNull` | `toNumberOrNull(str: String, formatters: Array<Formatter>): Number \| Null` | 2.5.0 |  | 1 |
| `toDateTime` | `toDateTime(str: String, formatters: Array<Formatter>): DateTime` | 2.5.0 |  | 3 |
|  | `toDateTime(number: Number, unit: MillisOrSecs \| Null = null): DateTime` | 2.4.0 |  |  |
|  | `toDateTime(str: String, format: String \| Null = null, locale: String \| Null = null): DateTime` | 2.4.0 |  |  |
| `toDateTimeOrNull` | `toDateTimeOrNull(str: String, formatters: Array<Formatter>): DateTime \| Null` | 2.5.0 |  | 1 |
| `toLocalDateTime` | `toLocalDateTime(str: String, formatters: Array<Formatter>): LocalDateTime` | 2.5.0 |  | 2 |
|  | `toLocalDateTime(str: String, format: String \| Null = null, locale: String \| Null = null): LocalDateTime` | 2.4.0 |  |  |
| `toLocalDateTimeOrNull` | `toLocalDateTimeOrNull(str: String, formatters: Array<Formatter>): LocalDateTime \| Null` | 2.5.0 |  | 1 |
| `toDate` | `toDate(str: String, formatters: Array<Formatter>): Date` | 2.5.0 |  | 2 |
|  | `toDate(str: String, format: String \| Null = null, locale: String \| Null = null): Date` | 2.4.0 |  |  |
| `toDateOrNull` | `toDateOrNull(str: String, formatters: Array<Formatter>): Date \| Null` | 2.5.0 |  | 1 |
| `toTime` | `toTime(str: String, formatters: Array<Formatter>): Time` | 2.5.0 |  | 2 |
|  | `toTime(str: String, format: String \| Null = null, locale: String \| Null = null): Time` | 2.4.0 |  |  |
| `toTimeOrNull` | `toTimeOrNull(str: String, formatters: Array<Formatter>): Time \| Null` | 2.5.0 |  | 1 |
| `toLocalTime` | `toLocalTime(str: String, formatters: Array<Formatter>): LocalTime` | 2.5.0 |  | 2 |
|  | `toLocalTime(str: String, format: String \| Null = null, locale: String \| Null = null): LocalTime` | 2.4.0 |  |  |
| `toLocalTimeOrNull` | `toLocalTimeOrNull(str: String, formatters: Array<Formatter>): LocalTime \| Null` | 2.5.0 |  | 1 |
| `toPeriod` | `toPeriod(str: String): Period` | 2.4.0 |  | 1 |
| `toRegex` | `toRegex(str: String): Regex` | 2.4.0 |  | 1 |
| `toBoolean` | `toBoolean(str: String): Boolean` | 2.4.0 |  | 1 |
| `toTimeZone` | `toTimeZone(str: String): TimeZone` | 2.4.0 |  | 1 |
| `toUri` | `toUri(str: String): Uri` | 2.4.0 |  | 1 |
| `toBinary` | `toBinary(str: String, encoding: String): Binary` | 2.4.0 |  | 1 |

## dw::util::Diff

doc: https://docs.mulesoft.com/dataweave/2.11/dw-diff

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `diff` | `diff(actual: Any, expected:Any, diffConfig: {unordered?: Boolean} = {}, path:String = "(root)"): Diff` |  |  | 1 |

## dw::util::Math

doc: https://docs.mulesoft.com/dataweave/2.11/dw-math

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `sin` | `sin(angle: Number):Number` | 2.4.0 |  | 1 |
| `cos` | `cos(angle: Number):Number` | 2.4.0 |  | 1 |
| `tan` | `tan(angle: Number):Number` | 2.4.0 |  | 1 |
| `asin` | `asin(angle: Number): Number \| NaN` | 2.4.0 |  | 1 |
| `acos` | `acos(angle: Number):Number \| NaN` | 2.4.0 |  | 1 |
| `atan` | `atan(angle: Number):Number` | 2.4.0 |  | 1 |
| `toRadians` | `toRadians(angdeg:Number): Number` | 2.4.0 |  | 1 |
| `toDegrees` | `toDegrees(angrad:Number):Number` | 2.4.0 |  | 1 |
| `logn` | `logn(a: Number): Number \| NaN` | 2.4.0 |  | 1 |
| `log10` | `log10(a: Number): Number \| NaN` | 2.4.0 |  | 1 |
| `decimalAdd` | `decimalAdd(lhs: Number, rhs: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalSubtract` | `decimalSubtract(lhs: Number, rhs: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalDivide` | `decimalDivide(dividend: Number, divisor: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalMultiply` | `decimalMultiply(leftFactor: Number, rightFactor: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalPow` | `decimalPow(base: Number, exponent: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalSqrt` | `decimalSqrt(n: Number, ctx: OperationContext = DECIMAL_128_CONTEXT): Number` |  |  | 1 |
| `decimalRound` | `decimalRound(n: Number, ctx: OperationContext = DECIMAL_128_CONTEXT)` |  |  | 1 |

## dw::util::Timer

doc: https://docs.mulesoft.com/dataweave/2.11/dw-timer

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `currentMilliseconds` | `currentMilliseconds(): Number` |  |  | 1 |
| `toMilliseconds` | `toMilliseconds(date:DateTime): Number` |  |  | 1 |
| `duration` | `duration<T>(valueToMeasure: ()-> T): DurationMeasurement<T>` |  |  | 1 |
| `time` | `time<T>(valueToMeasure: ()-> T): TimeMeasurement<T>` |  |  | 1 |

## dw::util::Tree

doc: https://docs.mulesoft.com/dataweave/2.11/dw-tree

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `asExpressionString` | `asExpressionString(path: Path): String` | 2.2.2 |  | 1 |
| `isAttributeType` | `isAttributeType(path: Path): Boolean` | 2.4.0 |  | 1 |
| `isObjectType` | `isObjectType(path: Path): Boolean` | 2.4.0 |  | 1 |
| `isArrayType` | `isArrayType(path: Path): Boolean` | 2.4.0 |  | 1 |
| `mapLeafValues` | `mapLeafValues(value: Any, callback: (value: Any, path: Path) -> Any): Any` | 2.2.2 |  | 2 |
| `filterTree` | `filterTree(value: Any, criteria: (value: Any, path: Path) -> Boolean): Any` | 2.4.0 |  | 1 |
| `filterObjectLeafs` | `filterObjectLeafs(value: Any, criteria: (value: Any, path: Path) -> Boolean): Any` | 2.4.0 |  | 1 |
| `filterArrayLeafs` | `filterArrayLeafs(value: Any, criteria: (value: Any, path: Path) -> Boolean): Any` | 2.4.0 |  | 1 |
| `nodeExists` | `nodeExists(value: Any, callback: (value: Any, path: Path) -> Boolean):Boolean` | 2.2.2 |  | 1 |

## dw::util::Values

doc: https://docs.mulesoft.com/dataweave/2.11/dw-values

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `attr` | `attr(namespace: Namespace \| Null = null, name: String): PathElement` | 2.2.2 |  | 1 |
| `field` | `field(namespace: Namespace \| Null = null, name: String): PathElement` | 2.2.2 |  | 1 |
| `index` | `index(index: Number): PathElement` | 2.2.2 |  | 1 |
| `mask` | `mask(value: Null, fieldName: String \| Number \| PathElement): (newValueProvider: (oldValue: Any, path: Path) -> Any) -> Null` | 2.2.2 |  | 3 |
|  | `mask(value: Any, selector: PathElement): (newValueProvider: (oldValue: Any, path: Path) -> Any) -> Any` | 2.2.2 |  |  |
|  | `mask(value: Any, fieldName: String): (newValueProvider: (oldValue: Any, path: Path) -> Any) -> Any` | 2.2.2 |  |  |
|  | `mask(value: Any, i: Number): (newValueProvider: (oldValue: Any, path: Path) -> Any) -> Any` | 2.2.2 |  |  |
| `update` | `update(objectValue: Object, fieldName: String): UpdaterValueProvider<Object>` | 2.2.2 |  | 7 |
|  | `update(objectValue: Object, fieldName: PathElement): UpdaterValueProvider<Object>` | 2.2.2 |  |  |
|  | `update(arrayValue: Array, indexToUpdate: Number): UpdaterValueProvider<Array>` | 2.2.2 |  |  |
|  | `update(arrayValue: Array, indexToUpdate: String): UpdaterValueProvider<Array>` | 2.2.2 |  |  |
|  | `update(arrayValue: Array, indexToUpdate: PathElement): UpdaterValueProvider<Array>` | 2.2.2 |  |  |
|  | `update(value: Array \| Object \| Null, path: Array<String \| Number \| PathElement>): UpdaterValueProvider< Array \| Object \| Null>` | 2.2.2 |  |  |
|  | `update(value: Null, toUpdate: Number \| String \| PathElement): UpdaterValueProvider<Null>` | 2.2.2 |  |  |

## dw::xml::Dtd

doc: https://docs.mulesoft.com/dataweave/2.11/dw-dtd

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `docTypeAsString` | `docTypeAsString(docType: DocType): String` | 2.5.0 |  | 2 |

## dw::Mule

doc: https://docs.mulesoft.com/dataweave/2.11/dw-mule

| 関数 | シグネチャ | 導入 | 状態 | 例 |
|---|---|---|---|---|
| `lookup` | `lookup(flowName: String, payload: Any, timeoutMillis: Number = 2000)` |  | 非推奨 (2.5.0〜) | 0 |
| `p` | `p(propertyName: String): String` |  |  | 0 |
| `causedBy` | `causedBy(@DesignOnlyType error: Error, errorType: String): Boolean` |  |  | 0 |

