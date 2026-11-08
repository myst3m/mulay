%dw 2.0
output application/json
var products = [
    {id: "P001", name: "Laptop", price: 1200.00, category: "electronics", stock: 50},
    {id: "P002", name: "T-Shirt", price: 25.00, category: "clothing", stock: 200},
    {id: "P003", name: "Apple", price: 1.50, category: "food", stock: 500}
]
var category = attributes.queryParams.category
---
if (category != null)
    products filter ((item) -> item.category == category)
else
    products