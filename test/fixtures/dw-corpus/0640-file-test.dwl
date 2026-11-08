%dw 2.0
output application/json
---
{status: "copied", source: vars.source, target: vars.target}