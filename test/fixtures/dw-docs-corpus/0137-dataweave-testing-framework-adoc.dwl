%dw 2.0
import * from dw::test::Tests
import * from dw::test::Asserts

import * from MyModule
---
"MyModule" describedBy [
   "something" describedBy [
       "It should do something" in do {
           something() must beObject()
       },
   ],
]