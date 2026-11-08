%dw 2.0
output application/json
---
{
  "a" : [0, 1, 2, 3] zip ["a", "b", "c", "d"],
  "b" : [0, 1, 2, 3] zip ["a"],
  "c" : [0, 1, 2, 3] zip ["a", "b"],
  "d" : [0, 1, 2] zip ["a", "b", "c", "d"]
}