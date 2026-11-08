%dw 2.0
output application/json
---
payload map ((item) -> {
    fileName: item.attributes.fileName,
    size: item.attributes.size,
    directory: item.attributes.directory
})