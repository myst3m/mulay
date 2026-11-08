%dw 2.0
output application/json
---
orderDescending: ([3,8,1] orderBy $)[-1 to 0]