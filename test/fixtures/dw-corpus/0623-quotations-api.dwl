%dw 2.0
output application/json
---
if (sizeOf(payload) > 0) payload[0] else null