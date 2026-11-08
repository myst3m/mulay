%dw 2.0
import * from dw::util::Coercions
output application/dw
---
{
  toRegexEx1: toRegex("a-Z"),
  toRegexEx2: toRegex("0-9+")
}