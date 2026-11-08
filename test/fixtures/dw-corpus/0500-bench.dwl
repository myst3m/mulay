%dw 2.0
output application/json
---
{
  source: "io-subflow",
  tag: vars.tag,
  upstream: payload
}