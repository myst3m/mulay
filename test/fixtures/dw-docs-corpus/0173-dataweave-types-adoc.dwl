%dw 2.0
output application/xml encoding="UTF-8"
---
file: {
  name: "transform",
  (extension: "zip") if payload.fileSystem?
}