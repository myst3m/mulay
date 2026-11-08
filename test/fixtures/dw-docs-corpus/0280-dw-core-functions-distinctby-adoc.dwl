%dw 2.0
output application/json
---
{a : "b", a : "b", A : "b", a : "B"} distinctBy (value) -> { "unique" : value }