%dw 2.0
output application/json
---
{status: "moved", source: vars.source, target: vars.target}