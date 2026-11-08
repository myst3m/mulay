%dw 2.0
import * from dw::core::Types
type AType = String | Number
output application/json
---
{
   a: isUnionType(AType),
   b: isUnionType(Boolean),
}