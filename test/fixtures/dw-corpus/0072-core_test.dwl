%dw 2.0
fun resolve(params) = params match {
  case obj is Object -> obj mapObject ((v, k) -> {(k): resolve(v)})
  case arr is Array -> arr map resolve($)
  else -> params
}
---
resolve({a: 1, b: {c: 2}, d: [3, 4]})