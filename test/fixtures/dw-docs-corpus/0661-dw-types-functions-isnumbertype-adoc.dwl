%dw 2.0
import * from dw::core::Types
type ANumber = Number
output application/json
---
{
   a: isNumberType(ANumber),
   b: isNumberType(Number),
   c: isNumberType(String),
}