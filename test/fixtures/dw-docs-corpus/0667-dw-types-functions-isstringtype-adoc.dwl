%dw 2.0
import * from dw::core::Types
type AString = String
output application/json
---
{
   a: isStringType(AString),
   b: isStringType(String),
   c: isStringType(Boolean),
}