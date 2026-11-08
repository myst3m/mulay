%dw 2.0

@StreamCapable()
input payload application/json
output application/json
---
[1,2,3] map ((item, index) -> payload)