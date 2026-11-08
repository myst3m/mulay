%dw 2.0
import * from dw::Runtime
var user = {}
var otherUser = {name: "DW"}
output application/json
---
{
    a: try(() -> user.name!) orElse "No User Name",
    b: try(() -> otherUser.name) orElse "No User Name"
}