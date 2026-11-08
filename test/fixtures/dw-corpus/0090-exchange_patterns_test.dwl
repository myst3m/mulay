%dw 2.0
fun mean(v) = if (isEmpty(v)) null else sum(v) / sizeOf(v)
fun variance(v) = do {
  var m = mean(v) default 0
  var devs = v map pow($ - m, 2)
  ---
  mean(devs)
}
---
{v: variance([1,2,3,2]), s: sqrt(variance([1,2,3,2]))}