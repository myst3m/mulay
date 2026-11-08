%dw 2.0
import * from dw::test::Tests
import * from dw::test::Asserts
---
"Test MyMapping" describedBy [
   "Assert NewScenario" in do {
       evalPath("myPackage/MyMapping.dwl", inputsFrom("myPackage/MyMapping/NewScenario"),"application/json") must
                 equalTo(outputFrom("myPackage/MyMapping/NewScenario"))
   }
]