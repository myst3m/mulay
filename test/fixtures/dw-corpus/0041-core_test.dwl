%dw 2.0
ns orders http://example.com/orders
ns items http://example.com/items
output application/xml
---
{orders#order: {items#item: "test"}}