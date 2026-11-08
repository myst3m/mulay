%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  a: toDate("2015-10-01"),
  b: toDate("2003/10/01","uuuu/MM/dd")
}