%dw 2.0
output application/json
---
"hello world!" groupBy (not isEmpty($ find /[aeiou]/))