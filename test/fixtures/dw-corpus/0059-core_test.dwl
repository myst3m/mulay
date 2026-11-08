%dw 2.0
---
payload.'timestamp' default today() as String {format: 'yyyy-MM-dd'}