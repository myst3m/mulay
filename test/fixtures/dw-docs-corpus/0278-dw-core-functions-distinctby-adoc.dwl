%dw 2.0
output application/json
---
[0, 1, 2, 3, 3, 2, 1, 4] distinctBy (value) -> { "unique" : value }