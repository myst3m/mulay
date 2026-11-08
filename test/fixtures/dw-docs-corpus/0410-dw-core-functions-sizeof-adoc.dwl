%dw 2.0
output application/json
---
{
  a: sizeOf(123),
  b: sizeOf(123.45)
}