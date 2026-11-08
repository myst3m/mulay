%dw 2.0
fun desc(n) = n match {
  case v if (v <= 0) -> "done"
  else -> desc(n - 1)
}
---
desc(3)