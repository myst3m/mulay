%dw 2.0
import * from avroschema!example::schema::User
---
{
 email: "john@acme.org",
 address: "123 Evergreen St.",
 telephone: "555 555 555"
} is User