%dw 2.0
var myJsonSnippet = readUrl("classpath://myJsonSnippet.json", "application/json")
output application/csv
---
(myJsonSnippet.results map(item) -> item.profile)