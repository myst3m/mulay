%dw 2.0
---
do {
  var intPart = 3
  var decPart = 5
  ---
  "$(intPart).$(decPart)" as Number as String
}