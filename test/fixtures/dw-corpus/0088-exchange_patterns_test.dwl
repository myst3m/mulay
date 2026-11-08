%dw 2.0
fun mean(v) = if (isEmpty(v)) null else sum(v) / sizeOf(v)
---
mean([])