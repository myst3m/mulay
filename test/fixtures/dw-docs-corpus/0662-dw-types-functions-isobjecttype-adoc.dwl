%dw 2.0
import * from dw::core::Types
type AType = {name: String}
output application/json
---
{
   a: isObjectType(AType),
   b: isObjectType(Boolean),
}