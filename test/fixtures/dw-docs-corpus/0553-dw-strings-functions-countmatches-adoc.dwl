%dw 2.0
import countMatches from dw::core::Strings
output application/json
---
"hello, ciao!" countMatches /[aeiou]/