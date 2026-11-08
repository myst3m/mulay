%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toDateOrNull("2023-28-03", [{format: "yyyy/MM/dd"}, {format: "yyyy-dd-MM", locale: "en_US"}]),
  b: toDateOrNull("2023-28-03", [{format: "yyyy/MM/dd"}])
}