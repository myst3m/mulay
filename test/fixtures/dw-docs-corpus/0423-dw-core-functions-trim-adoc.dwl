%dw 2.0
output application/json
---
{ "trim": trim("   my really long  text     ") }