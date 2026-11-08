%dw 2.0
---
"hello" replace /[a-z]+/ with ((m) -> upper(m[0]))