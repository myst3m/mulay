%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toLocalDateTime("2015-10-01T23:57:59"),
  b: toLocalDateTime("2003-10-01 23:57:59","uuuu-MM-dd HH:mm:ss")
}