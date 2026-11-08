%dw 2.0
import * from avroschema!example::schema::User
---
{
 name: "John",
 email: "john@acme.org"
} is User