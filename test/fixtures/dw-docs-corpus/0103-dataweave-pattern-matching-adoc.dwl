%dw 2.0
var myInput = {
  "string": "Emiliano",
  "number": 3.14
}
output application/json
---
{
  a: myInput.string match {
    case str if str == "Mariano" -> str ++ " de Achaval"
    case str if str == "Emiliano" -> str ++ " Lesende"
  },
  b: myInput.number match {
    case num if num == 3 -> "equal"
    case num if num > 3 -> "greater than"
    case num if num < 3 -> "less than"
  }
}