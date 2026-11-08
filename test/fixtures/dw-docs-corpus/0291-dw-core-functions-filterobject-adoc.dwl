%dw 2.0
output application/json
---
{"a" : "apple", "b" : "banana"} filterObject ((value) -> value == "apple")