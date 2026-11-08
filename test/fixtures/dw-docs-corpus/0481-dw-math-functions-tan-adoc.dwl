%dw 2.0
import * from dw::util::Math
output application/json
---
{
   "tan0": tan(0),
   "tan13": tan(0.13),
   "tan-1": tan(-1)
}