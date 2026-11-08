%dw 2.5
output application/json

fun max<T>(elems: Array<T>): T = elems reduce ((candidate: T, currentMax = elems[0]) -> if (candidate > currentMax) candidate else currentMax)
---
{
  max: max<Number>(measures)
}