%dw 2.0
import * from dw::core::Strings
output application/json
---
"12 34  56" everyCharacter $ == " " or isNumeric($)