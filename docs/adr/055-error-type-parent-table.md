# 055 — エラー型の親子関係は、実物の jar の enum と実行時の parentErrorType から表に書く

状態: **採用** (2026-09-28。コネクタの節は各コネクタを足した日。MS-VECTORS は 2026-10-10 ebf554d)

## 決定
- エラー型 `NS:ID` の親は `mulay.rt.error/PARENTS` の表で持つ。値は推測で決めず、コネクタの ErrorTypeDefinition の enum を
  tools/gen-error-types で実物の jar から取り出して書く。表に無い型 (APP:* や未知のコネクタの型) の親は ANY。
- 照合は型そのものか祖先に一致すれば成立する。CRITICAL 系 (CRITICAL、OVERLOAD、FLOW_BACK_PRESSURE、FATAL_JVM_ERROR) は ANY に一致しない。
- enum と実行時の型の表が違うときは、実行時の値 (実 Mule の `error.errorType.parentErrorType`) に合わせる:
  - `MULE:RETRY_EXHAUSTED`: MuleErrors の enum では ANY の直下だが、実行時 (CoreErrorTypeRepository) は CONNECTIVITY の子。
    until-successful を使い果たしたときの parentErrorType で確かめた。
  - ANYPOINT-MQ の PUBLISHING / CONSUMING / ACKING / NACKING / DESTINATION_NOT_FOUND の親は ANY (parentErrorType で確かめた)。
- 表の出どころ (クラスと版):

| 名前空間 | クラス | 版 |
|---|---|---|
| MULE | org.mule.runtime.extension.api.error.MuleErrors と core の内部型 | Mule 4.11.3 |
| HTTP | org.mule.extension.http.api.error.HttpError | mule-http-connector 1.11.3 |
| VALIDATION | org.mule.extension.validation.api.ValidationErrorType | mule-validation-module 2.0.11 |
| MS-VECTORS | org.mule.extension.vectors.internal.error.MuleVectorsErrorType | mule4-vectors-connector 1.0.0 |
| WSC | org.mule.extension.ws.internal.error.WscError | mule-wsc-connector 2.2.2 |
| SALESFORCE-COMPOSITE | CompositeErrorType | mule-salesforce-composite-connector 3.1.4 |
| ANYPOINT-MQ | com.mulesoft.extension.mq.api.exception.AnypointMQError | anypoint-mq-connector 4.0.23 |

- 親が ANY のものは表に書かない (MS-VECTORS の TRANSFORM_OPERATIONS_FAILURE、EMBEDDING_OPERATIONS_FAILURE、
  STORE_OPERATIONS_FAILURE など、WSC の CONNECTIVITY・RETRY_EXHAUSTED・EMPTY_RESPONSE 以外、SALESFORCE-COMPOSITE の UNKNOWN と TRANSACTION)。

## 理由
- on-error の type の照合は親子関係で決まる。推測した親は、実 Mule で捕まるエラーを捕まえない (または逆) 不具合になる。

## 場所
- `mulay.rt.error`: `PARENTS`、`norm-type`、`matches?`
- tools/gen-error-types/README.md
