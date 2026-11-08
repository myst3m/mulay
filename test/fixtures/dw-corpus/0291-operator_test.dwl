%dw 2.0
---
"hello world" replace /(\w+)/ with ((m,i) -> "[" ++ m[1] ++ "]")