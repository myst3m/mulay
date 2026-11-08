%dw 2.0
fun clamp(val, minVal = 0, maxVal = 100) =
  if (val < minVal) minVal
  else if (val > maxVal) maxVal
  else val
---
clamp(50)