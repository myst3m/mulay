%dw 2.0
fun frequencies(values) = do {
  var uniques = values distinctBy $
  ---
  uniques map {
    value: $,
    occurrences: sizeOf(values find $)
  }
}
fun modes(values) = do {
  var freq = frequencies(values)
  var maxOcc = freq map $.occurrences maxBy $
  ---
  freq filter ($.occurrences == maxOcc) map $.value
}
---
modes(["a","b","c","a","b"])