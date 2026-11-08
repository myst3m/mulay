%dw 2.0
import * from dw::core::Types
type AKey = Key
output application/json
---
{
   a: isKeyType(AKey),
   b: isKeyType(Key),
   c: isKeyType(Boolean),
}