%dw 2.0
import dw::tests::Asserts
---
[1,2,3] must eachItem(beNumber())