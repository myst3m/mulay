%dw 2.0
output application/json
var data = (1 to 2000) map {
  id: $,
  val: $ * $ * 0.37,
  cat: if (($ mod 7) == 0) "x" else if (($ mod 5) == 0) "y" else "z"
}
var filtered = data filter $.cat != "z"
var totals = filtered reduce ((item, acc = {sum: 0, count: 0}) -> {
  sum: acc.sum + item.val,
  count: acc.count + 1
})
var sorted = filtered orderBy $.val
---
{
  avg: totals.sum / totals.count,
  count: totals.count,
  min: sorted[0].val,
  max: sorted[-1].val
}