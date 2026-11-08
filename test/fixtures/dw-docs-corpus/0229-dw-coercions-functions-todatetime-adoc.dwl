%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
   a: toDateTime("2015-10-01T23:57:59Z"),
   b: toDateTime("2003-10-01 23:57:59Z","uuuu-MM-dd HH:mm:ssz")
}