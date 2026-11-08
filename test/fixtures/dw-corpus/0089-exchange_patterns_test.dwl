%dw 2.0
fun frequencies(values) = do {
  var uniques = values distinctBy $
  ---
  uniques map {
    value: $,
    occurrences: sizeOf(values find $)
  }
}
---
frequencies([1, 2, 11, 1, 1, 2])