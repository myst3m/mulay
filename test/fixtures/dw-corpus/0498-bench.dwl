%dw 2.0
output application/json
---
{
  source: "io-pipeline",
  upstream: payload,
  processed: true
}