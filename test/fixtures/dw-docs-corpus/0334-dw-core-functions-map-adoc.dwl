%dw 2.0
output application/json
---
['joe', 'pete', 'matt'] map ( "$$" : $)