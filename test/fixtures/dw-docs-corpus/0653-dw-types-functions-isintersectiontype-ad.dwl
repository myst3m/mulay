%dw 2.0
import * from dw::core::Types
type AType = {name: String} & {age: Number}
output application/json
---
{
   a: isIntersectionType(AType),
   b: isIntersectionType(Boolean),
}