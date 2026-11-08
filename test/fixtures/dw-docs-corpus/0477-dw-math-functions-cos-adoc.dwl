%dw 2.0
import * from dw::util::Math
output application/json
---
{
  "cos0": cos(0),
  "cos13": cos(0.13),
  "cos-1": cos(-1)
}