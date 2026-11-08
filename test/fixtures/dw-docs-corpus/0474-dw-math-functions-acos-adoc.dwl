%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "acos0": acos(0),
  "acos13": acos(0.13),
  "acos-1": acos(-1),
  "acos1": acos(1),
  "acos1.1": acos(1.1)
}