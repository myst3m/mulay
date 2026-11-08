%dw 2.0
output application/json
---
friends: payload.friends.*name map (
            (item, index) -> {name: item}
         )