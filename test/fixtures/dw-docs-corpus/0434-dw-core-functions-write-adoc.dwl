%dw 2.0
output application/json
---
{ hello : write("world", "text/plain") }