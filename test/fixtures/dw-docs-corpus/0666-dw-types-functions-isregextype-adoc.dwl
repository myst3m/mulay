%dw 2.0
import * from dw::core::Types
type ARegex = Regex
output application/json
---
{
   a: isRegexType(ARegex),
   b: isRegexType(Regex),
   c: isRegexType(Boolean),
}