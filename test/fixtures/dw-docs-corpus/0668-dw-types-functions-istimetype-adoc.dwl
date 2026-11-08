%dw 2.0
import * from dw::core::Types
type ATime = Time
output application/json
---
{
   a: isTimeType(ATime),
   b: isTimeType(Time),
   c: isTimeType(String),
}