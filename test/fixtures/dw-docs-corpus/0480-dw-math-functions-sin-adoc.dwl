%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "sin0": sin(0),
  "sin13": sin(0.13),
  "sin-1": sin(-1)
}