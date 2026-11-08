%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toDateTimeOrNull("2003-10-01 23:57:59Z", [{format: "uuuu/MM/dd HH:mm:ssz"}, {format: "uuuu-MM-dd HH:mm:ssz"}]),
  b: toDateTimeOrNull("2003-10-01 23:57:59Z", [{format: "uuuu/MM/dd HH:mm:ssz"}])
}