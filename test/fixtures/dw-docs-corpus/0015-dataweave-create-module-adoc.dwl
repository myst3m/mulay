%dw 2.0
import modules::MyMapping
output application/json
---
MyMapping::main(payload: { "user" : "bar" })