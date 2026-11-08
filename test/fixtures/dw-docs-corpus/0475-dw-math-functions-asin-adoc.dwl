%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "asin0": asin(0),
  "asin13": asin(0.13),
  "asin-1": asin(-1),
  "asin1.1": asin(1.1)
}