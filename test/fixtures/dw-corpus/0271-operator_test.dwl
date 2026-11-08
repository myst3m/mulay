%dw 2.0
---
"hello" match {
  case is String -> "it's a string"
  case is Number -> "it's a number"
  else -> "unknown"
}