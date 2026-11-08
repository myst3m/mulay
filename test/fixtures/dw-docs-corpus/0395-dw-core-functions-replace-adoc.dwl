%dw 2.0
output application/json
---
[ "my123" replace /(\d+)/ with("ID"), replace("myOther123", /(\d+)/) with("ID") ]