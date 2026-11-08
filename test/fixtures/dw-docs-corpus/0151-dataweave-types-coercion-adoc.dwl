%dw 2.0
output application/json
---
"8/30/2020 4:00:13 PM"
    as LocalDateTime {format: "M/dd/uuuu h:mm:ss a"}
    as String {format: "MM/dd/uuuu"}