%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
  a: toString([]),
  b: toString(["h", "o", "l", "a"])
}