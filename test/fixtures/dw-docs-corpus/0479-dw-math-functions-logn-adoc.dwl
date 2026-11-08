%dw 2.0
import * from dw::util::Math
output application/json
---
{
   "logn10":  logn(10),
   "logn13": logn(0.13),
   "logn-20": logn(-20)
}