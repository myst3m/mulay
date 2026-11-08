%dw 2.0
import * from dw::Runtime
var user = {}
var otherUser = {}
output application/json
---
{
    a: try(() -> user.name!) orElseTry otherUser.name!,
    b: try(() -> user.name!) orElseTry "No User Name"
}