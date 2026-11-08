%dw 2.0
import * from dw::util::Coercions
var binaryData= "DW Test" as Binary {encoding: "UTF-32"}
output application/json
---
{
  a: toString(binaryData, "UTF-32"),
}