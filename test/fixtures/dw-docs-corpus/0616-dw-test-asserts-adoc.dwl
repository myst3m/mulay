%dw 2.0
import dw::tests::Asserts
---
[1, true, "a text"] must haveItem(beNumber())