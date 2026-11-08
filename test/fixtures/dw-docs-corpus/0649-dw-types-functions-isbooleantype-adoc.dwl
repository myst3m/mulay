%dw 2.0
import * from dw::core::Types
type ABoolean = Boolean
output application/json
---
{
   a: isBooleanType(ABoolean),
   b: isBooleanType(Boolean),
   c: isBooleanType(String),
}