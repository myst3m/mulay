%dw 2.0
import * from dw::util::Coercions
import * from dw::Runtime
output application/dw
---
{
  a: toDate("2023-28-03", [{format: "yyyy/MM/dd"}, {format: "yyyy-dd-MM", locale: "en_US"}]),
  b: try(() -> toDate("2023-28-03", [{format: "yyyy/MM/dd"}])).error.message
}