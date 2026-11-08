%dw 2.0
output application/json
---
{
  source: "io-simple",
  upstream: payload
}