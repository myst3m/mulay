%dw 2.0
---
"a b c" replace /(\w)/ with ((m,i) -> m[1] ++ i)