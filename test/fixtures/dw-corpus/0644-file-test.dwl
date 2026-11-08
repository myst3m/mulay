%dw 2.0
output application/json
---
{status: "renamed", path: vars.path, newName: vars.newName}