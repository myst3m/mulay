%dw 2.0
output application/json
---
{
  count: sizeOf(payload),
  total: sum(payload map $.price),
  names: payload map upper($.name)
}
