%dw 2.0
---
[{name: "a", price: 10}, {name: "b", price: 20}] map do {
  var item = $
  ---
  {
    label: item.name,
    total: item.price * 2
  }
}