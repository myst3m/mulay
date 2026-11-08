%dw 2.0
output application/json
var greeting = "Hello"
var count = 10
---
{
  message: greeting,
  total: count * 2
}