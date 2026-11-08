%dw 2.0
import * from dw::core::Types
type APeriod = Period
output application/json
---
{
   a: isPeriodType(APeriod),
   b: isPeriodType(Period),
   c: isPeriodType(String),
}