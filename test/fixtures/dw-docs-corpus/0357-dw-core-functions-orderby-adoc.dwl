%dw 2.0
output application/json
---
[{ letter: "e" }, { letter: "d" }] orderBy($.letter)