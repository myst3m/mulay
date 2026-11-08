%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toLocalDateTimeOrNull("2003-10-01 23:57:59", [{format: "uuuu/MM/dd HH:mm:ss"}, {format: "uuuu-MM-dd HH:mm:ss"}]),
  b: toLocalDateTimeOrNull("2003-10-01 23:57:59", [{format: "uuuu/MM/dd HH:mm:ss"}])
}