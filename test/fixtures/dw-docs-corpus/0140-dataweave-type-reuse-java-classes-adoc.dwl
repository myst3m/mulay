%dw 2.0
output json
import java!org::mycompany::Product
 
var aBook: Product::Class = {name: "Learn DW", price: 123}
fun description(p: Product::Class) = "The product: $(p.name), costs: $(p.price)"
 
type Order = {
    product: Product::Class,
    date: LocalDateTime
}
---
{
    a: Product::new("DW lang", 321) is Product::Class,
    b: description(aBook),
    c: {product: aBook, date: |2022-12-18T14:00:00|} is Order
}