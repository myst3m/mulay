%dw 2.0
output application/json
---
"hello world" reduce (item, acc = "") -> item ++ acc