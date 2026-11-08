%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "log1010": log10(10),
  "log1013": log10(0.13),
  "log10-20": log10(-20)
}