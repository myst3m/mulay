%dw 2.0
output application/json
---
"hello world" filter ($$ mod 2) == 0