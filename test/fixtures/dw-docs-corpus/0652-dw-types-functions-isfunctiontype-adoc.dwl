%dw 2.0
import * from dw::core::Types
type AFunction = (String) -> String
output application/json
---
{
   a: isFunctionType(AFunction),
   b: isFunctionType(Boolean)
}