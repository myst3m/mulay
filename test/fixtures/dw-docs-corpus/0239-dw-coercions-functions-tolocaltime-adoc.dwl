%dw 2.0
import * from dw::util::Coercions
import * from dw::Runtime
output application/dw
---
{
  a: toLocalTime("23:57:59", [{format: "HH:mm:ss.n"}, {format: "HH:mm:ss"}]),
  b: try(() -> toLocalTime("23:57:59", [{format: "HH:mm:ss.n"}])).error.message
}