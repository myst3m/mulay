%dw 2.0
output application/json
var x = 42
var items = [{a: 1}, {a: 2}]
---
{
  x: x,
  mapped: items map $.a
}