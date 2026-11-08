%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "toRadians10":  toRadians(10),
  "toRadians013": toRadians(0.13),
  "toRadians-20": toRadians(-20)
}