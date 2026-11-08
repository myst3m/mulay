%dw 2.0
import * from dw::core::Types
type ADate = Date
output application/json
---
{
   a: isDateType(ADate),
   b: isDateType(Date),
   c: isDateType(String),
}