%dw 2.0
output application/json
type Currency = String { format: "\$#,###.00"}
---
books: payload.items.*item map
    book:
        price: $.price as Currency