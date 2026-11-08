%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toNumberOrNull("0.005", [{format: "seconds"}, {format: ".00"}]),
  b: toNumberOrNull("0.005", [{format: "seconds"}])
}