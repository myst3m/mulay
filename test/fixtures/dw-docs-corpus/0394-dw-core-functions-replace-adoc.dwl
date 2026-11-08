%dw 2.0
output application/json
---
["123-456-7890" replace /.*-/ with(""), "abc123def" replace /[b13e]/ with("-")]