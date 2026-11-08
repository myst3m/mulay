%dw 2.0
import * from jsonschema!example::schema::Person
---
{
 firstName: "John",
 lastName: "Doe"
} is Root