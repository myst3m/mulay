%dw 2.0
import * from dw::util::Coercions
import * from dw::Runtime
output application/dw
---
{
  a: toNumber("0.005", [{format: "seconds"}, {format: ".00"}]),
  b: try(() -> toNumber("0.005", [{format: "seconds"}])).error.message
}