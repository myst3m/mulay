%dw 2.0
fun abs(n) = if (n >= 0) n else -1 * n
---
abs(-7)