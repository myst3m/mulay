%dw 2.0
var myInput = {
  "string": "Emiliano"
}
output application/json
---
{
  a: myInput.string match {
    case "Emiliano" -> true
    case "Mariano" -> false
  },
  b: myInput.string match {
    case str: "Emiliano" -> { "matches": true, value: str }
    case str: "Mariano" -> { "matches": false, value: str }
  }
}