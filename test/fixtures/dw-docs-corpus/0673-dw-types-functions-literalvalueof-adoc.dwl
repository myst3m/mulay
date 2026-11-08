%dw 2.0
import * from dw::core::Types
type AType = "Mariano"
output application/json
---
{
   a: literalValueOf(AType)
}