%dw 2.0
import dw::tests::Asserts
---
"A Text" must anyOf(beObject(), beString())