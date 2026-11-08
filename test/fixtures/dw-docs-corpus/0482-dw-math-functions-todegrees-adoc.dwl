%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "toDegrees0.17":  toDegrees(0.174),
  "toDegrees0": toDegrees(0),
  "toDegrees-20": toDegrees(-0.20)
}