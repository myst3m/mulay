%dw 2.0
fun fact(n) = if (n <= 1) 1 else n * fact(n - 1)
---
fact(5)