%dw 2.0
output application/json
---
{"letter1": "a", "letter2": "b", "id": 1} filterObject ((value, key) -> key startsWith "letter")