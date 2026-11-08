%dw 2.0
---
"hello 123" replace /[a-z]+/ with ((m,i) -> upper(m[0]))