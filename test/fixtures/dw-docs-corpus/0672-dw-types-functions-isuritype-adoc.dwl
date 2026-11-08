%dw 2.0
import * from dw::core::Types
type AUri = Uri
output application/json
---
{
   a: isUriType(AUri),
   b: isUriType(Uri),
   c: isUriType(String),
}