%dw 2.0
output application/json
---
readUrl("https://mywebsite.com/data.csv", "application/csv", {"header" : false})