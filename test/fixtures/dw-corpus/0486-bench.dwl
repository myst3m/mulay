%dw 2.0
output application/json
---
payload filter $.active map {
  id: $.id,
  name: upper($.name),
  total: $.price * $.quantity,
  tier: if ($.price > 200) "premium" else if ($.price > 100) "standard" else "basic"
}