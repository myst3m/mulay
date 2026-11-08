%dw 2.0
---
do {
  fun sum(n) = if (n <= 0) 0 else n + sum(n - 1)
  ---
  sum(10)
}