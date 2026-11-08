%dw 2.0
import * from dw::core::Types
type ALiteralType = "Mariano"
output application/json
---
{
   a: isLiteralType(ALiteralType),
   b: isLiteralType(Boolean)
}