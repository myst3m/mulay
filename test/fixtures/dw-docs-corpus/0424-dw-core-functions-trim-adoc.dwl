%dw 2.0
output application/json
---
{
  "null": trim(null),
  "empty": trim(""),
  "blank": trim("     "),
  "noBlankSpaces": trim("abc"),
  "withSpaces": trim("    abc    ")
}