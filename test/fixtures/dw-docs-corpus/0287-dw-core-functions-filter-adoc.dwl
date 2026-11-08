%dw 2.0
output application/json
---
[9, 2, 3, 4, 5] filter (($$ > 1) and ($ < 5))