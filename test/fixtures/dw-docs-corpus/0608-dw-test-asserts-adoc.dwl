%dw 2.0
import dw::tests::Asserts
---
1 must beOneOf([1, "A Text", true])