%dw 2.0
output application/json
---
{
  items: (1 to 100) map {
    id: $,
    name: "item-" ++ ($ as String),
    price: $ * 10.5,
    category: if (($ mod 3) == 0) "A" else if (($ mod 3) == 1) "B" else "C"
  },
  summary: {
    total: sizeOf(1 to 100),
    avgPrice: avg((1 to 100) map ($ * 10.5))
  }
}