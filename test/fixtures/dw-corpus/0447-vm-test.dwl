%dw 2.0
output application/json
---
{
  echo: payload,
  processed: true,
  timestamp: now()
}