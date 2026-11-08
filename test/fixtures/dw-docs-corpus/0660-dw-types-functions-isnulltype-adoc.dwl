%dw 2.0
import * from dw::core::Types
type ANull = Null
output application/json
---
{
   a: isNullType(ANull),
   b: isNullType(Null),
   c: isNullType(String),
}