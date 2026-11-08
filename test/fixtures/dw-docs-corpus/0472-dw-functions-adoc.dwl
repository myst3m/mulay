%dw 2.0
import pluralize from dw::core::Strings
output application/json
---
{ 'plural': pluralize("box") }