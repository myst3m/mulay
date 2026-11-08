%dw 2.0
output application/json
var name = "Shoki"
---
{
    Greeting: "Hi, my name is $name",
    Sum: "1 + 1 = $(1 + 1)"
}