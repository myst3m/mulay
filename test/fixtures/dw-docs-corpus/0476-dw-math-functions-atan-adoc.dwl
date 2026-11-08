%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "atan0":  atan(0),
  "atan13": atan(0.13),
  "atan-1": atan(-1)
}