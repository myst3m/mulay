%dw 2.0

@StreamCapable()
input payload application/json
output application/json
---
 {
     family: payload.family filter (member) -> member.age > 3,
     name: payload.name
 }