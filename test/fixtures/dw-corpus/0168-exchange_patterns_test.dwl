%dw 2.0
---
{
  payment: (round(1.17 * (payload.amount as Number) / (payload.term as Number) * 100)) / 100,
  currency: "EUR"
}