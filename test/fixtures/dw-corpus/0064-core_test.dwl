%dw 2.0
fun double(n) = n * 2
fun quadruple(n) = double(double(n))
---
quadruple(3)