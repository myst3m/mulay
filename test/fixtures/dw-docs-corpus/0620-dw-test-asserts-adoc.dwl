%dw 2.0
import dw::tests::Asserts
---
payload must [
    beObject(),
    $.foo is Null
]