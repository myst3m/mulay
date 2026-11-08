%dw 2.0
import * from jsonschema!example::schema::Account
---
{
 firstName: "John",
 lastName: "Doe"
} match {
case is person -> "PERSON"
case is address -> "ADDRESS"
else -> "NO TYPE MATCHED"
}