%dw 2.0
import * from jsonschema!example::schema::Account
---
{
 street_address: "742 Evergreen Terrace",
 city: "Gotham",
 State: "OH"
} match {
case is person -> "PERSON"
case is address -> "ADDRESS"
else -> "NO TYPE MATCHED"
}