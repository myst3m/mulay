%dw 2.0
fun mean(v) = if (isEmpty(v)) null else sum(v) / sizeOf(v)
---
mean([1,2,3,4,5])