%dw 2.0
---
1 match {
  case 1 -> "one"
  case 2 -> "two"
  else -> "other"
}