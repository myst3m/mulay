%dw 2.0
import dw::tests::Asserts
---
{ name: "Lionel", lastName: "Messi" } must equalToResource("user.json", "application/json")