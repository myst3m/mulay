%dw 2.0
import * from dw::core::Types
type ALocalDateTime = LocalDateTime
output application/json
---
{
   a: isLocalDateTimeType(ALocalDateTime),
   b: isLocalDateTimeType(LocalDateTime),
   c: isLocalDateTimeType(String),
}