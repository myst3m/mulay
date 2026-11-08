%dw 2.0
import * from dw::util::Coercions
output application/json indent=false
---
{
  a: toArray(""),
  b: toArray("hola")
}