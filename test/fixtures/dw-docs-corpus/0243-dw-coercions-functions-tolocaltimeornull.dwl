%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toLocalTimeOrNull("23:57:59", [{format: "HH:mm:ss.n"}, {format: "HH:mm:ss"}]),
  b: toLocalTimeOrNull("23:57:59", [{format: "HH:mm:ss.n"}])
}