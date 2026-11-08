%dw 2.0
output application/json
---
{
  status: "ok",
  timestamp: now() as String,
  method: attributes.method
}