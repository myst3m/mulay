%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
  a: toBoolean("true"),
  b: toBoolean("false"),
  c: toBoolean("FALSE"),
  d: toBoolean("TrUe")
}