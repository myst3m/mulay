%dw 2.0
output application/json
fun toUpper(aString)
= aString match {
  case is String -> upper(aString)
  else -> null
}
---
toUpper("h" ++ "el" ++ lower("LO") )