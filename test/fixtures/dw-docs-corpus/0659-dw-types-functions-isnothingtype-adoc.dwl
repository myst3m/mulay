%dw 2.0
import * from dw::core::Types
type ANothing = Nothing
output application/json
---
{
   a: isNothingType(ANothing),
   b: isNothingType(Nothing),
   c: isNothingType(String),
}