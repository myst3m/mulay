%dw 2.0
output application/json
---
{ ContainsString : payload.root.mystring contains("me") }