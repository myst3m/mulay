%dw 2.0
output application/json
---
{count: payload[0].TOTAL}