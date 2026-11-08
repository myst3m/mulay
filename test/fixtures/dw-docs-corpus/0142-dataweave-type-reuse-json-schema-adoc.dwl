%dw 2.0
import * from jsonschema!example::schema::Person
---
{
 firstName: "John",
 age: 20
} is Root