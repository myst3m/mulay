%dw 2.0
---
[{year: 2003, price: 10}, {year: 2005, price: 20}, {year: 2006, price: 30}]
  filter ($.year > 2004)
  map { title: "book", cost: $.price * 1.1 }