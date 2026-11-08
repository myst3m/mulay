%dw 2.0
output application/json
---
{
    id: "P" ++ (random() * 1000) as String {format: "000"},
    name: payload.name,
    price: payload.price,
    category: payload.category default "electronics",
    stock: payload.stock default 0
}