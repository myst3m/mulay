%dw 2.0
import dw::core::Strings
output application/json
---
{ 'plural': Strings::pluralize("box") }