%dw 2.0
import * from dw::core::Types
type ALocalTime = LocalTime
output application/json
---
{
   a: isLocalTimeType(ALocalTime),
   b: isLocalTimeType(LocalTime),
   c: isLocalTimeType(String),
}