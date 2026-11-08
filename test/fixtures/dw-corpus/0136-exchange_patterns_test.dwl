%dw 2.0
fun pickRandom(options) = options[randomInt(sizeOf(options))]
---
{
  pick: pickRandom(["a","b","c"]),
  randBase: floor(5) + randomInt(10 - 5)
}