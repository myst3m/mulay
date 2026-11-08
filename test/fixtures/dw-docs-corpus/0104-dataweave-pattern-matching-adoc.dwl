%dw 2.0
var myInput =
{
  "a": "Emiliano",
  "b": 3.14
}
output application/json
---
{
  a: myInput.a match {
    case is Object -> 'OBJECT'
    case is String -> 'STRING'
    case is Number -> 'NUMBER'
    case is Boolean -> 'BOOLEAN'
    case is Array -> 'ARRAY'
    case is Null -> 'NULL'
    else -> 'ANOTHER TYPE'
  },
  b: myInput.b match {
    case y is Object -> { 'Type': { 'OBJECT' : y} }
    case y is String -> { 'Type': { 'STRING' : y} }
    case y is Number -> { 'Type': { 'NUMBER' : y} }
    case y is Boolean -> { 'Type': { 'BOOLEAN' : y} }
    case y is Array -> { 'Type': { 'ARRAY' : y} }
    case y is Null -> { 'Type': { 'NULL' : y} }
    else -> { 'Type': { 'ANOTHER TYPE' : myInput.b} }
  }
}