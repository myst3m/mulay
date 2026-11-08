%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  'UTF-16Ex': toBinary("DW", "UTF-16"),
  'utf16Ex': toBinary("DW", "utf16"),
  'UnicodeBigEx': toBinary("DW", "UnicodeBig"),
  'UTF-32Ex': toBinary("DW", "UTF-32"),
  'UTF_32Ex': toBinary("DW", "UTF_32")
}