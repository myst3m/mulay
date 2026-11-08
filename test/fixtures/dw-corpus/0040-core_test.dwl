%dw 2.0
ns orders http://example.com/orders
output application/xml
---
{orders#order: {orders#id: "123"}}