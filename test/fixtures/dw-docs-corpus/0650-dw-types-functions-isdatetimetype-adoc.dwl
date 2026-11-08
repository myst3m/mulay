%dw 2.0
import * from dw::core::Types
type ADateTime = DateTime
output application/json
---
{
   a: isDateTimeType(ADateTime),
   b: isDateTimeType(DateTime),
   c: isDateTimeType(String),
}