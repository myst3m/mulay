%dw 2.0
output application/json
var x = [
  {b: "b"},
  {c: "c", d: "d"}
]
var y = {e: "e"}
---
{
  a: "a",
  (x),
  (y)
}