%dw 2.0
output application/json
---
{ "1": "a", "2": "b", "3": "c"} filterObject ((value, key, index) -> index < 1)