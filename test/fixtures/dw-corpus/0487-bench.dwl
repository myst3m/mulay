%dw 2.0
output application/json
---
sizeOf(payload filter ($.price * $.quantity > 500))