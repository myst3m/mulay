%dw 2.0
output application/json
---
(1 to vars.inputSize) map {
  id: $,
  name: "product-" ++ ($ as String),
  price: ($ * 7.3) + 0.99,
  quantity: ($ mod 20) + 1,
  active: ($ mod 5) != 0
}