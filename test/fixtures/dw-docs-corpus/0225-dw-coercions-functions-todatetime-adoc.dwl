%dw 2.0
import * from dw::util::Coercions
import * from dw::Runtime
output application/dw
---
{
  a: toDateTime("2003-10-01 23:57:59Z", [{format: "uuuu/MM/dd HH:mm:ssz"}, {format: "uuuu-MM-dd HH:mm:ssz"}]),
  b: try(() -> toDateTime("2003-10-01 23:57:59Z", [{format: "uuuu/MM/dd HH:mm:ssz"}])).error.message
}