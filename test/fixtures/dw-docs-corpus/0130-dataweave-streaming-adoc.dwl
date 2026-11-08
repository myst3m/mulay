%dw 2.0

@StreamCapable()
input payload application/json
output application/json
---
payload.family filter (member) -> member.age > 3