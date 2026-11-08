%dw 2.0
output application/json
---
ContainsRequestedItem: payload.root.*order.*items contains "3"