%dw 2.0
var myVar = { menu: {
    header: "Move Items",
    items: [
        {"id": "internal"},
        {"id": "left", "label": "Move Left"},
        {"id": "right", "label": "Move Right"},
        {"id": "up", "label": "Move Up"},
        {"id": "down", "label": "Move Down"}
    ]
}}
output application/json
---
(myVar.menu.items.*label groupBy "myLabels")