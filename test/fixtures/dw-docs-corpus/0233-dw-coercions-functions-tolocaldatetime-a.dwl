%dw 2.0
import * from dw::util::Coercions
import * from dw::Runtime
output application/dw
---
{
  a: toLocalDateTime("2003-10-01 23:57:59", [{format: "uuuu/MM/dd HH:mm:ss"}, {format: "uuuu-MM-dd HH:mm:ss"}]),
  b: try(() -> toLocalDateTime("2003-10-01 23:57:59", [{format: "uuuu/MM/dd HH:mm:ss"}])).error.message
}