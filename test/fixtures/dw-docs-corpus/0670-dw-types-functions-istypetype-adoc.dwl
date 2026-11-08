%dw 2.0
import * from dw::core::Types
type AType = Type
output application/json
---
{
   a: isTypeType(AType),
   b: isTypeType(Type),
   c: isTypeType(String),
}