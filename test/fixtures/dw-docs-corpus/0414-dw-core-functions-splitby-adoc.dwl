%dw 2.0
output application/json
---
'root.sources.data.`test.branch.BranchSource`.source.traits' splitBy(/[.](?=(?:[^`]*`[^`]*`)*[^`]*$)/)