%dw 2.0
output application/json
fun double(x) = x * 2
fun add(a, b) = a + b
---
{
  doubled: double(5),
  sum: add(3, 4)
}