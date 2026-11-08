%dw 2.0
---
42 match {
  case s is String -> "str"
  case n is Number -> "num"
  else -> "other"
}